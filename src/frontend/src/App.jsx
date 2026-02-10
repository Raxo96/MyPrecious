import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import PortfolioList from './pages/PortfolioList'
import PortfolioOverview from './pages/PortfolioOverview'
import AssetSearch from './pages/AssetSearch'
import AssetDetail from './pages/AssetDetail'
import AddTransaction from './pages/AddTransaction'
import FetcherMonitoring from './pages/FetcherMonitoring'
import { ToastProvider } from './components/ToastContainer'
import KeyboardShortcuts from './components/KeyboardShortcuts'

function App() {
  return (
    <Router>
      <ToastProvider>
        <div className="min-h-screen bg-gray-50">
          <Header />
          <main className="container mx-auto px-4 py-8">
            <Routes>
              <Route path="/" element={<PortfolioList />} />
              <Route path="/portfolios/:id" element={<PortfolioOverview />} />
              <Route path="/assets" element={<AssetSearch />} />
              <Route path="/assets/:symbol" element={<AssetDetail />} />
              <Route path="/transactions/new" element={<AddTransaction />} />
              <Route path="/fetcher" element={<FetcherMonitoring />} />
            </Routes>
          </main>
          <KeyboardShortcuts />
        </div>
      </ToastProvider>
    </Router>
  )
}

export default App