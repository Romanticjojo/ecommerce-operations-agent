import { useState } from 'react'
import { ArrowRight, ArrowUpRight } from 'lucide-react'
import type { Overview as OverviewData } from './api'
import { dateOnly, number, percent, sourceName } from './api'
import { BarChart, Empty, ErrorBox, Fold, PageHead, Pending, Table, Trend } from './ui'

export function Overview({ data, error, retry }: { data?: OverviewData; error: string; retry: () => void }) {
  const [metric, setMetric] = useState<'item_revenue' | 'order_count'>('item_revenue')
  const coverage = data && [sourceName(data.source), data.start && data.end
    ? `Purchases from ${dateOnly(data.start)} to ${dateOnly(data.end)}` : 'Purchase dates unavailable'].join(' · ')
  return <div className="overview-report">
    <PageHead title="Operations overview" sub={coverage} action={<a className="primary" href="#ask">Ask the agent<ArrowRight size={16}/></a>}/>
    {error ? <ErrorBox message={error} retry={retry}/> : !data ? <Pending/> :
      !data.order_count && !data.monthly?.length ? <div className="panel"><Empty title="No delivered orders" action={<a className="quiet" href="#ask/data">View data setup<ArrowRight size={15}/></a>}>Import a snapshot with delivered orders to see sales and review metrics.</Empty></div> :
      <>
        <div className="sales-spread">
          <section className="sales-total">
            <h2>Item revenue <small>BRL</small></h2>
            <strong className="report-amount">{number(data.item_revenue, 2)}</strong>
            <p>Sum of item prices for delivered orders, excluding freight.</p>
            <dl className="sales-context">
              <div><dt>Delivered orders</dt><dd><strong>{number(data.order_count)}</strong></dd></div>
              <div><dt>Average order value</dt><dd><strong>{number(data.aov, 2)}</strong> BRL</dd></div>
            </dl>
          </section>
          <section className="sales-trend">
            <div className="panel-head"><h2>Monthly sales trend</h2>
              <div className="seg" role="group" aria-label="Trend metric">{(['item_revenue', 'order_count'] as const).map((m, i) =>
                <button key={m} aria-pressed={metric === m} onClick={() => setMetric(m)}>{i ? 'Orders' : 'Revenue'}</button>
              )}</div>
            </div>
            <Trend rows={data.monthly || []} x="month" y={metric} unit={metric === 'item_revenue' ? 'BRL' : 'orders'}/>
            <Fold title="View monthly data"><Table rows={data.monthly} caption="Monthly sales and orders"/></Fold>
          </section>
        </div>
        <div className="report-details">
          <section className="category-report">
            <div className="panel-head"><h2>Revenue by category</h2><p>Top five · BRL</p></div>
            <BarChart rows={(data.categories || []).slice(0, 5)} x="category" y="item_revenue" formatter={v => number(v, 2)}/>
            <Fold title="View category data"><Table rows={data.categories} caption="Category revenue"/></Fold>
          </section>
          <section className="delivery-report">
            <h2>Delivery and reviews</h2>
            <div className="review-metric"><strong>{percent(data.negative_rate)}</strong><span>of eligible orders had a negative review</span></div>
            <p>Includes delivered orders with both delivery timestamps and a valid review. The latest eligible review counts once per order. Scores of 1 or 2 are negative.</p>
            <a className="report-link" href="#ask/delivery">Compare deliveries in Ask the agent<ArrowRight size={16}/></a>
          </section>
        </div>
        <footer className="report-footer"><a className="report-link" href="#ask/data">Open data reference in Ask the agent<ArrowUpRight size={15}/></a></footer>
      </>}
  </div>
}
