// Column labels rendered as React Flow nodes so they pan/zoom with the flow
// content. This keeps every sub-column header aligned with its column at any
// zoom level, without any separate DOM tracking of the viewport.

interface Data {
  isFirstOfMeta: boolean;
  isCollapsedSummary: boolean;
  metaLabel: string;
  subLabel: string;
  width: number;
}

export function ColumnLabelNode({ data }: { data: Data }) {
  return (
    <div
      className={`glance-column-label-node ${data.isFirstOfMeta ? "is-first-of-meta" : ""}`}
      style={{ width: data.width }}
    >
      {data.isFirstOfMeta && (
        <div className="glance-column-label-meta">{data.metaLabel}</div>
      )}
      {!data.isCollapsedSummary && (
        <div className="glance-column-label-sub">{data.subLabel}</div>
      )}
    </div>
  );
}
