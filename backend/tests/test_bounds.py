"""Test 7 — Bounds. Values that must live in specific ranges."""


def test_every_hhi_and_concentration_in_unit_interval(graph):
    offenders = []
    for node in graph.nodes.values():
        d = node.dynamic
        for name, val in [
            ("inbound_hhi", d.inbound_hhi),
            ("outbound_criticality", d.outbound_criticality),
            ("concentration", d.concentration),
            ("combined_hhi", d.combined_hhi),
            ("mined_by_hhi", d.mined_by_hhi),
            ("refined_by_hhi", d.refined_by_hhi),
            ("supplied_by_hhi", d.supplied_by_hhi),
        ]:
            if val is None:
                continue
            if not (0.0 <= val <= 1.0):
                offenders.append((node.id, name, val))
        # stage_hhis dict
        for stage, v in (d.stage_hhis or {}).items():
            if not (0.0 <= v <= 1.0):
                offenders.append((node.id, f"stage_hhis[{stage}]", v))
    assert not offenders, offenders[:5]


def test_severity_non_negative(graph):
    offenders = [
        (n.id, n.dynamic.current_severity)
        for n in graph.nodes.values()
        if (n.dynamic.current_severity or 0.0) < 0.0
    ]
    assert not offenders, offenders


def test_edge_weights_in_open_zero_to_one(graph):
    offenders = []
    for e in graph.edges.values():
        if not (0.0 < e.weight <= 1.0):
            offenders.append((e.id, e.weight))
    assert not offenders, offenders[:5]


def test_static_axes_in_unit_interval(graph):
    offenders = []
    for node in graph.nodes.values():
        for field_name in ("substitutability", "financial_cushion"):
            sv = getattr(node.static, field_name)
            if sv is None or sv.value is None:
                continue
            try:
                v = float(sv.value)
            except (TypeError, ValueError):
                continue
            if not (0.0 <= v <= 1.0):
                offenders.append((node.id, field_name, v))
    assert not offenders, offenders[:5]
