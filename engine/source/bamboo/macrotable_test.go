/*
 * SPDX-FileCopyrightText: 2026 Nguyen Hoang Ky <nhktmdzhg@gmail.com>
 *
 * SPDX-License-Identifier: LGPL-2.1-or-later
 *
 */
package main

import "testing"

func TestMacroTableEmpty(t *testing.T) {
	var nilTable *MacroTable
	if !nilTable.Empty() {
		t.Errorf("nil MacroTable: Empty() got [false] expected [true]")
	}
	if !(&MacroTable{}).Empty() {
		t.Errorf("empty MacroTable: Empty() got [false] expected [true]")
	}
	nonEmpty := &MacroTable{mTable: map[string]string{"vn": "Việt Nam"}}
	if nonEmpty.Empty() {
		t.Errorf("non-empty MacroTable: Empty() got [true] expected [false]")
	}
}

func TestMacroTableGet(t *testing.T) {
	table := &MacroTable{mTable: map[string]string{"vn": "Việt Nam"}}

	if val, ok := table.Get("VN"); !ok || val != "Việt Nam" {
		t.Errorf("Get(VN) got [%s,%v] expected [Việt Nam,true] (case-insensitive)", val, ok)
	}
	if _, ok := table.Get("vn"); !ok {
		t.Errorf("Get(vn) got [missing] expected [found]")
	}
	if _, ok := table.Get(""); ok {
		t.Errorf("Get(empty key) got [found] expected [missing]")
	}
	if _, ok := table.Get("xyz"); ok {
		t.Errorf("Get(xyz) got [found] expected [missing]")
	}
	if _, ok := (&MacroTable{}).Get("vn"); ok {
		t.Errorf("Get on empty table got [found] expected [missing]")
	}
}

func TestMacroTableKeyWrittenWithCapitals(t *testing.T) {
	table := &MacroTable{mTable: map[string]string{}}
	table.add("VN", "Việt Nam")
	table.add("KO", "Kansas")
	table.add("ko", "không")
	table.add("Ko", "Korea")
	for _, key := range []string{"vn", "Vn", "VN"} {
		if val, ok := table.Get(key); !ok || val != "Việt Nam" {
			t.Errorf("Get(%s) got [%s,%v] expected [Việt Nam,true]", key, val, ok)
		}
	}
	if val, _ := table.Get("KO"); val != "không" {
		t.Errorf("Get(KO) got [%s] expected the lower-case key's [không]", val)
	}
}

func TestMacroTableFirstCapitalizedKeyWins(t *testing.T) {
	table := &MacroTable{mTable: map[string]string{}}
	table.add("KO", "Kansas")
	table.add("Ko", "Korea")
	if val, _ := table.Get("ko"); val != "Kansas" {
		t.Errorf("Get(ko) got [%s] expected the first key's [Kansas]", val)
	}
}
