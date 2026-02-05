<script>
	import { onMount } from 'svelte';
	import { createChart } from 'lightweight-charts';

	export let data = [];
	export let title = 'Chart';
	export let height = 300;

	let chartContainer;
	let chart;
	let series;

	onMount(() => {
		chart = createChart(chartContainer, {
			width: chartContainer.clientWidth,
			height: height,
			layout: {
				background: { color: '#ffffff' },
				textColor: '#333'
			},
			grid: {
				vertLines: { color: '#f0f0f0' },
				horzLines: { color: '#f0f0f0' }
			},
			timeScale: {
				timeVisible: true,
				secondsVisible: false
			}
		});

		console.log('Chart object:', chart);
		console.log('addLineSeries exists?', typeof chart.addLineSeries);

		series = chart.addLineSeries({
			color: '#3b82f6',
			lineWidth: 2
		});

		if (data.length > 0) {
			series.setData(data);
			chart.timeScale().fitContent();
		}

		const handleResize = () => {
			chart.applyOptions({ width: chartContainer.clientWidth });
		};

		window.addEventListener('resize', handleResize);

		return () => {
			window.removeEventListener('resize', handleResize);
			chart.remove();
		};
	});

	$: if (series && data.length > 0) {
		series.setData(data);
		chart.timeScale().fitContent();
	}
</script>

<div class="chart-wrapper">
	<h3>{title}</h3>
	<div bind:this={chartContainer} class="chart-container"></div>
</div>

<style>
	.chart-wrapper {
		margin: 1rem 0;
	}

	h3 {
		margin: 0 0 0.5rem 0;
		font-size: 1rem;
		color: #666;
	}

	.chart-container {
		width: 100%;
		border-radius: 8px;
		overflow: hidden;
	}
</style>
