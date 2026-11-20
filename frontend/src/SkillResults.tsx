import { useState } from 'react'
import { ChevronFirst, ChevronLast, ChevronLeft, ChevronRight } from 'lucide-react'
import type { Row } from './api'
import { number } from './api'
import { Fold, Table, Trend } from './ui'

const PAGE_SIZE = 15
const scoreColumns = ['rank', 'seller_id', 'score', 'rating_component', 'delivery_component', 'rated_orders', 'timed_orders']

export function MerchantRanking({ rows }: { rows: Row[] }) {
  const [page, setPage] = useState(0)
  const [allColumns, setAllColumns] = useState(false)
  const first = page * PAGE_SIZE
  const last = Math.min(rows.length, first + PAGE_SIZE)
  const lastPage = Math.ceil(rows.length / PAGE_SIZE) - 1
  const visible = rows.slice(first, last)
  const scorecard = visible.map(row => Object.fromEntries(scoreColumns.filter(k => k in row).map(k => [k, row[k]])))
  return <section className="ranking-data" aria-label="Merchant leaderboard">
    <div className="panel-head compact"><h3>Merchant leaderboard</h3>
      <label className="column-choice"><input type="checkbox" checked={allColumns} onChange={e => setAllColumns(e.target.checked)}/>Show all columns</label></div>
    <Table rows={allColumns ? visible : scorecard} caption="Merchant leaderboard data"/>
    <div className="rank-footer"><span role="status">Showing {number(first + 1)}–{number(last)} of {number(rows.length)} sellers</span>
      {lastPage > 0 && <nav aria-label="Leaderboard pages">
        <button type="button" disabled={page === 0} aria-label="First page" onClick={() => setPage(0)}><ChevronFirst size={17}/></button>
        <button type="button" disabled={page === 0} aria-label="Previous page" onClick={() => setPage(page - 1)}><ChevronLeft size={17}/></button>
        <button type="button" disabled={page === lastPage} aria-label="Next page" onClick={() => setPage(page + 1)}><ChevronRight size={17}/></button>
        <button type="button" disabled={page === lastPage} aria-label="Last page" onClick={() => setPage(lastPage)}><ChevronLast size={17}/></button>
      </nav>}
    </div>
  </section>
}

export function ProductOutlook({ rows }: { rows: Row[] }) {
  const [index, setIndex] = useState(0)
  const product = rows[index]
  const monthly = ['first', 'middle', 'latest'].map(key => ({ month: product[key + '_month'], units: product[key + '_units'] }))
  return <section className="product-outlook" aria-label="Product sales outlook">
    <h3>Inspect a product</h3>
    <div className="product-selector"><label htmlFor="outlook-product">Product</label><select id="outlook-product" value={index} onChange={e => setIndex(Number(e.target.value))}>
      {rows.map((r, i) => <option key={String(r.product_id)} value={i}>{String(r.category).replaceAll('_', ' ')} · {String(r.product_id)}</option>)}
    </select></div>
    {monthly.every(r => typeof r.month === 'string' && typeof r.units === 'number') && <Trend rows={monthly} x="month" y="units" unit="units sold"/>}
    <div className="product-decision" aria-live="polite"><h3>Plan for {String(product.planning_month).slice(0,7)}</h3>
      <p>{String(product.next_action)}.</p><small>Three-month median · {number(product.planning_units)} units</small></div>
    <Fold title="View product data"><Table rows={rows} caption="Product sales and planning data"/></Fold>
  </section>
}
