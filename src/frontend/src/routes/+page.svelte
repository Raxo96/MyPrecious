<script>
	import { onMount } from 'svelte';
	import Chart from '$lib/Chart.svelte';
	
	const API_URL = 'http://localhost:8000';
	
	let portfolioValue = 0;
	let portfolioCost = 0;
	let portfolioPL = 0;
	let portfolioPLPct = 0;
	let dayChange = 0;
	let positions = [];
	let assets = [];
	let portfolioHistory = [];
	let searchQuery = '';
	let selectedAsset = '';
	let quantity = '';
	let price = '';
	let date = new Date().toISOString().split('T')[0];
	let loading = false;
	
	$: filteredAssets = searchQuery 
		? assets.filter(a => 
			a.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
			a.name.toLowerCase().includes(searchQuery.toLowerCase())
		)
		: [];
	
	onMount(async () => {
		await loadPortfolio();
		await loadPositions();
		await loadAssets();
		await loadPortfolioHistory();
	});
	
	async function loadPortfolio() {
		try {
			const res = await fetch(`${API_URL}/api/portfolios/1`);
			const data = await res.json();
			portfolioValue = data.total_value;
			portfolioCost = data.total_cost;
			portfolioPL = data.total_profit_loss;
			portfolioPLPct = data.total_profit_loss_pct;
			dayChange = data.day_change;
		} catch (e) {
			console.error('Failed to load portfolio:', e);
		}
	}
	
	async function loadPositions() {
		try {
			const res = await fetch(`${API_URL}/api/portfolios/1/positions`);
			const data = await res.json();
			positions = data.positions;
		} catch (e) {
			console.error('Failed to load positions:', e);
		}
	}
	
	async function loadAssets() {
		try {
			const res = await fetch(`${API_URL}/api/assets/search`);
			const data = await res.json();
			assets = data.assets;
		} catch (e) {
			console.error('Failed to load assets:', e);
		}
	}
	
	async function loadPortfolioHistory() {
		try {
			const res = await fetch(`${API_URL}/api/portfolios/1/history?days=30`);
			const data = await res.json();
			portfolioHistory = data.history;
		} catch (e) {
			console.error('Failed to load portfolio history:', e);
		}
	}
	
	async function handleSubmit() {
		if (!selectedAsset || !quantity || !price) return;
		
		loading = true;
		try {
			const asset = assets.find(a => a.symbol === selectedAsset);
			const res = await fetch(`${API_URL}/api/transactions?portfolio_id=1`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					asset_id: asset.id,
					quantity: parseFloat(quantity),
					price: parseFloat(price),
					timestamp: new Date(date).toISOString()
				})
			});
			
			if (res.ok) {
				alert('Transaction added successfully!');
				selectedAsset = '';
				quantity = '';
				price = '';
				await loadPortfolio();
				await loadPositions();
			}
		} catch (e) {
			alert('Failed to add transaction: ' + e.message);
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Portfolio Tracker</title>
</svelte:head>

<div class="container">
	<header>
		<h1>📊 Portfolio Tracker</h1>
		<p class="subtitle">Track your investments in real-time</p>
	</header>

	<main>
		<!-- Portfolio Overview -->
		<section class="card">
			<h2>My Portfolio</h2>
			<div class="portfolio-summary">
				<div class="stat">
					<span class="label">Total Value</span>
					<span class="value">${portfolioValue.toLocaleString('en-US', {minimumFractionDigits: 2})}</span>
				</div>
				<div class="stat">
					<span class="label">Total Cost</span>
					<span class="value">${portfolioCost.toLocaleString('en-US', {minimumFractionDigits: 2})}</span>
				</div>
				<div class="stat">
					<span class="label">Profit/Loss</span>
					<span class="value {portfolioPL >= 0 ? 'positive' : 'negative'}">
						{portfolioPL >= 0 ? '+' : ''}${portfolioPL.toLocaleString('en-US', {minimumFractionDigits: 2})}
					</span>
					<span class="change {portfolioPLPct >= 0 ? 'positive' : 'negative'}">
						{portfolioPLPct >= 0 ? '+' : ''}{portfolioPLPct.toFixed(2)}%
					</span>
				</div>
			</div>
		</section>

		<!-- Portfolio Chart -->
		{#if portfolioHistory.length > 0}
		<section class="card">
			<Chart data={portfolioHistory} title="Portfolio Value (30 Days)" height={300} />
		</section>
		{/if}

		<!-- Positions List -->
		<section class="card">
			<h2>Positions</h2>
			<div class="positions-list">
				{#if positions.length > 0}
					{#each positions as position}
						<div class="position-item">
							<div class="position-info">
								<span class="symbol">{position.symbol}</span>
								<span class="name">{position.name}</span>
							</div>
							<div class="position-details">
								<span>{position.quantity} @ ${position.average_buy_price.toFixed(2)}</span>
								<span class="value">${position.value.toFixed(2)}</span>
								<span class="change {position.profit_loss >= 0 ? 'positive' : 'negative'}">
									{position.profit_loss >= 0 ? '+' : ''}${position.profit_loss.toFixed(2)}
									({position.profit_loss_pct >= 0 ? '+' : ''}{position.profit_loss_pct.toFixed(2)}%)
								</span>
							</div>
						</div>
					{/each}
				{:else}
					<p class="empty-state">No positions yet. Add your first transaction below!</p>
				{/if}
			</div>
		</section>

		<!-- Asset Search -->
		<section class="card">
			<h2>Search Assets</h2>
			<input 
				type="text" 
				bind:value={searchQuery}
				placeholder="Search stocks (e.g., AAPL, MSFT)..."
				class="search-input"
			/>
			{#if filteredAssets.length > 0}
				<div class="search-results">
					{#each filteredAssets as asset}
						<div class="asset-item">
							<div>
								<span class="symbol">{asset.symbol}</span>
								<span class="name">{asset.name}</span>
							</div>
							<span class="price">${asset.current_price.toFixed(2)}</span>
						</div>
					{/each}
				</div>
			{/if}
		</section>

		<!-- Add Transaction -->
		<section class="card">
			<h2>Add Transaction</h2>
			<form on:submit|preventDefault={handleSubmit} class="transaction-form">
				<div class="form-group">
					<label for="asset">Asset</label>
					<select id="asset" bind:value={selectedAsset} required>
						<option value="">Select asset...</option>
						{#each assets as asset}
							<option value={asset.symbol}>{asset.symbol} - {asset.name}</option>
						{/each}
					</select>
				</div>
				<div class="form-group">
					<label for="quantity">Quantity</label>
					<input type="number" id="quantity" bind:value={quantity} step="0.00000001" required />
				</div>
				<div class="form-group">
					<label for="price">Price</label>
					<input type="number" id="price" bind:value={price} step="0.01" required />
				</div>
				<div class="form-group">
					<label for="date">Date</label>
					<input type="date" id="date" bind:value={date} required />
				</div>
				<button type="submit" class="btn-primary" disabled={loading}>
					{loading ? 'Adding...' : 'Add Transaction'}
				</button>
			</form>
		</section>
	</main>
</div>

<style>
	:global(body) {
		margin: 0;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
		background: #f5f5f5;
		color: #333;
	}

	.container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
	}

	header {
		text-align: center;
		margin-bottom: 3rem;
	}

	h1 {
		font-size: 2.5rem;
		margin: 0;
		color: #1a1a1a;
	}

	.subtitle {
		color: #666;
		margin-top: 0.5rem;
	}

	main {
		display: grid;
		gap: 2rem;
	}

	.card {
		background: white;
		border-radius: 12px;
		padding: 2rem;
		box-shadow: 0 2px 8px rgba(0,0,0,0.1);
	}

	h2 {
		margin-top: 0;
		font-size: 1.5rem;
		color: #1a1a1a;
	}

	.portfolio-summary {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 2rem;
		margin-top: 1.5rem;
	}

	.stat {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.label {
		font-size: 0.875rem;
		color: #666;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.value {
		font-size: 2rem;
		font-weight: 600;
		color: #1a1a1a;
	}

	.change {
		font-size: 1.5rem;
	}

	.positive {
		color: #10b981;
	}

	.negative {
		color: #ef4444;
	}

	.positions-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		margin-top: 1rem;
	}

	.position-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem;
		background: #f9fafb;
		border-radius: 8px;
	}

	.position-info {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.symbol {
		font-weight: 600;
		font-size: 1.125rem;
	}

	.name {
		font-size: 0.875rem;
		color: #666;
	}

	.position-details {
		display: flex;
		gap: 1.5rem;
		align-items: center;
		font-size: 0.875rem;
	}

	.search-input {
		width: 100%;
		padding: 0.75rem;
		font-size: 1rem;
		border: 2px solid #e5e7eb;
		border-radius: 8px;
		margin-top: 1rem;
	}

	.search-input:focus {
		outline: none;
		border-color: #3b82f6;
	}

	.search-results {
		margin-top: 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.asset-item {
		display: flex;
		justify-content: space-between;
		padding: 1rem;
		background: #f9fafb;
		border-radius: 8px;
		cursor: pointer;
		transition: background 0.2s;
	}

	.asset-item:hover {
		background: #f3f4f6;
	}

	.price {
		font-weight: 600;
	}

	.transaction-form {
		display: grid;
		gap: 1.5rem;
		margin-top: 1.5rem;
	}

	.form-group {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	label {
		font-weight: 500;
		font-size: 0.875rem;
		color: #374151;
	}

	input, select {
		padding: 0.75rem;
		font-size: 1rem;
		border: 2px solid #e5e7eb;
		border-radius: 8px;
	}

	input:focus, select:focus {
		outline: none;
		border-color: #3b82f6;
	}

	.btn-primary {
		padding: 0.875rem 1.5rem;
		font-size: 1rem;
		font-weight: 600;
		color: white;
		background: #3b82f6;
		border: none;
		border-radius: 8px;
		cursor: pointer;
		transition: background 0.2s;
	}

	.btn-primary:hover {
		background: #2563eb;
	}

	.btn-primary:disabled {
		background: #9ca3af;
		cursor: not-allowed;
	}

	.empty-state {
		text-align: center;
		color: #9ca3af;
		padding: 2rem;
		font-style: italic;
	}

	@media (max-width: 768px) {
		.container {
			padding: 1rem;
		}

		h1 {
			font-size: 2rem;
		}

		.position-item {
			flex-direction: column;
			align-items: flex-start;
			gap: 1rem;
		}
	}
</style>
