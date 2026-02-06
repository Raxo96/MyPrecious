import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import PortfolioOverview from './pages/PortfolioOverview'
import AssetSearch from './pages/AssetSearch'
import AssetDetail from './pages/AssetDetail'
import AddTransaction from './pages/AddTransaction'
import FetcherMonitoring from './pages/FetcherMonitoring'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<PortfolioOverview />} />
            <Route path="/assets" element={<AssetSearch />} />
            <Route path="/assets/:symbol" element={<AssetDetail />} />
            <Route path="/transactions/new" element={<AddTransaction />} />
            <Route path="/fetcher" element={<FetcherMonitoring />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App