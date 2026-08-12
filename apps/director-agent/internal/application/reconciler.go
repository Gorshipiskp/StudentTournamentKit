package application

import (
	"context"
	"log"
	"sync"

	"github.com/bestcstournaments/director-agent/internal/domain"
	"github.com/bestcstournaments/director-agent/internal/infrastructure/obs"
)

// Reporter sends observed actual state to Platform.
type Reporter interface {
	ReportActual(ctx context.Context, actual domain.Actual, obsStatus string) error
}

// Reconciler applies Platform desired.scene to OBS (A12: desired is SoT).
type Reconciler struct {
	obs      obs.Controller
	reporter Reporter

	mu      sync.Mutex
	desired domain.Desired
}

func NewReconciler(ctrl obs.Controller, reporter Reporter) *Reconciler {
	return &Reconciler{
		obs:      ctrl,
		reporter: reporter,
		desired:  domain.Desired{Scene: domain.SceneWaiting, Stream: "off"},
	}
}

func (r *Reconciler) SetDesired(d domain.Desired) {
	r.mu.Lock()
	r.desired = d
	r.mu.Unlock()
}

func (r *Reconciler) Desired() domain.Desired {
	r.mu.Lock()
	defer r.mu.Unlock()
	return r.desired
}

// ApplyDesired reconciles OBS to current desired and reports actual.
// On Agent restart the Platform pushes desired again — we never replay a command log.
func (r *Reconciler) ApplyDesired(ctx context.Context) error {
	d := r.Desired()
	if d.Scene == "" {
		d.Scene = domain.SceneWaiting
	}

	current, err := r.obs.GetCurrentProgramScene(ctx)
	if err != nil {
		return err
	}
	if current != d.Scene {
		log.Printf("reconcile: OBS scene %q → desired %q", current, d.Scene)
		if err := r.obs.SetCurrentProgramScene(ctx, d.Scene); err != nil {
			return err
		}
		current = d.Scene
	} else {
		log.Printf("reconcile: already at desired scene %q", d.Scene)
	}

	actual := domain.Actual{Scene: current, Stream: d.Stream}
	if actual.Stream == "" {
		actual.Stream = "off"
	}
	if r.reporter != nil {
		if err := r.reporter.ReportActual(ctx, actual, r.obs.Status()); err != nil {
			log.Printf("report actual failed: %v", err)
			return err
		}
	}
	return nil
}
