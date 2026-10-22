package main

import "testing"

func TestNormalizeMessage(t *testing.T) {
	cases := []struct{ in, want string }{
		{"upstream timed out (110: Connection timed out) while reading 0x7f3a2c and 12345", "upstream timed out (<n>: Connection timed out) while reading <addr> and <n>"},
		{"job 42 failed", "job <n> failed"},
		{"disk quota exceeded", "disk quota exceeded"},
	}
	for _, c := range cases {
		if got := normalizeMessage(c.in); got != c.want {
			t.Errorf("normalizeMessage(%q) = %q, want %q", c.in, got, c.want)
		}
	}
}

func TestGroupingMergesSimilarMessages(t *testing.T) {
	groups := map[string]*Group{}
	add := func(unit, msg string) {
		m := normalizeMessage(msg)
		key := unit + "|" + m
		if g, ok := groups[key]; ok {
			g.Count++
			return
		}
		groups[key] = &Group{Unit: unit, Message: m, Count: 1}
	}
	add("nginx.service", "upstream timed out for 7788")
	add("nginx.service", "upstream timed out for 9911")
	add("postgres.service", "connection refused")

	if len(groups) != 2 {
		t.Fatalf("ожидалось 2 группы, получили %d", len(groups))
	}
	if g := groups["nginx.service|upstream timed out for <n>"]; g == nil || g.Count != 2 {
		t.Fatalf("nginx-группа не склеилась: %+v", g)
	}
}

func TestPolicyRejectsInjection(t *testing.T) {
	if _, err := RunReadOnly("journalctl", "-n","5", "-p","err; rm -rf /"); err == nil {
		t.Fatal("аргумент с ';' должен быть отклонён")
	}
	if _, err := RunReadOnly("bash", "-c", "id"); err == nil {
		t.Fatal("bash не должен быть в белом списке")
	}
	if _, err := RunReadOnly("df", "-h"); err != nil {
		t.Fatalf("df должен быть разрешён: %v", err)
	}
}

func TestUnitNameValidation(t *testing.T) {
	p := &Policy{Mode: "readonly"}
	if _, err := UnitStatus("nginx.service; reboot", p); err == nil {
		t.Fatal("инъекция в имени юнита должна отклоняться")
	}
}
