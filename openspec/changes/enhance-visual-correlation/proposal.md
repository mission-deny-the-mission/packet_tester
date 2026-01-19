# Change: Enhance Visual Correlation

## Why
Users need to quickly identify exactly where in the network path a problem begins. A single destination chart makes this difficult. Stacked sparklines for every hop allow for vertical correlation of latency spikes.

## What Changes
- **Stacked Sparklines**: Every hop in the Path Analysis table will get a mini-chart.
- **Synchronized Timelines**: All charts within a target card will share the same X-axis (time).
- **Correlation Highlighting**: Hovering over one chart will highlight the corresponding time on all other charts in the card.

## Impact
- Affected specs: `hop-analysis`
- Affected code: `dashboard.js`, `templates/index.html`
