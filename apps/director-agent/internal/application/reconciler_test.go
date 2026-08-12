package application_test

import (
	"context"
	"testing"

	"github.com/bestcstournaments/director-agent/internal/application"
	"github.com/bestcstournaments/director-agent/internal/domain"
	"github.com/bestcstournaments/director-agent/internal/infrastructure/obs"
)

type memReporter struct {
	last domain.Actual
	obs  string
	n    int
}

func (m *memReporter) ReportActual(ctx context.Context, actual domain.Actual, obsStatus string) error {
	_ = ctx
	m.last = actual
	m.obs = obsStatus
	m.n++
	return nil
}

func TestReconcileAppliesDesiredScene(t *testing.T) {
	fake := obs.NewFakeOBS("waiting")
	if err := fake.Connect(context.Background()); err != nil {
		t.Fatal(err)
	}
	rep := &memReporter{}
	rec := application.NewReconciler(fake, rep)
	rec.SetDesired(domain.Desired{Scene: "intro", Stream: "off"})
	if err := rec.ApplyDesired(context.Background()); err != nil {
		t.Fatal(err)
	}
	if fake.Scene() != "intro" {
		t.Fatalf("fake scene=%q want intro", fake.Scene())
	}
	if rep.last.Scene != "intro" || rep.n != 1 {
		t.Fatalf("report=%+v n=%d", rep.last, rep.n)
	}
}

func TestRestartAppliesDesiredNotHistory(t *testing.T) {
	// A12: restart = apply current desired once, no command replay.
	fake := obs.NewFakeOBS("waiting")
	_ = fake.Connect(context.Background())
	rep := &memReporter{}
	rec := application.NewReconciler(fake, rep)

	rec.SetDesired(domain.Desired{Scene: "ingame", Stream: "off"})
	_ = rec.ApplyDesired(context.Background())

	// Simulate agent restart: new reconciler, Platform pushes desired again
	rec2 := application.NewReconciler(fake, rep)
	rec2.SetDesired(domain.Desired{Scene: "ingame", Stream: "off"})
	if err := rec2.ApplyDesired(context.Background()); err != nil {
		t.Fatal(err)
	}
	if fake.Scene() != "ingame" {
		t.Fatalf("after restart scene=%q", fake.Scene())
	}
	if rep.n < 2 {
		t.Fatalf("expected report after restart, n=%d", rep.n)
	}
}
