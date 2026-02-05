import { Link, useLocation } from 'react-router-dom'

function Header() {
  const location = useLocation()

  const isActive = (path) => location.pathname === path

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="text-xl font-bold text-primary">
            MyPrecious
          </Link>
          
          <nav className="flex space-x-8">
            <Link
              to="/"
              className={`px-3 py-2 rounded-md text-sm font-medium ${
                isActive('/') 
                  ? 'text-primary bg-blue-50' 
                  : 'text-gray-600 hover:text-primary'
              }`}
            >
              Portfolio
            </Link>
            <Link
              to="/assets"
              className={`px-3 py-2 rounded-md text-sm font-medium ${
                isActive('/assets') 
                  ? 'text-primary bg-blue-50' 
                  : 'text-gray-600 hover:text-primary'
              }`}
            >
              Assets
            </Link>
            <Link
              to="/transactions/new"
              className="bg-primary text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-600"
            >
              Add Transaction
            </Link>
          </nav>
        </div>
      </div>
    </header>
  )
}

export default Header