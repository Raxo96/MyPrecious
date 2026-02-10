import { useState, useEffect } from 'react'

function KeyboardShortcuts() {
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    const handleKeyPress = (e) => {
      // Show shortcuts help with Shift + ?
      if (e.shiftKey && e.key === '?') {
        e.preventDefault()
        setIsOpen(prev => !prev)
      }
      // Close with ESC
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false)
      }
    }

    document.addEventListener('keydown', handleKeyPress)
    return () => document.removeEventListener('keydown', handleKeyPress)
  }, [isOpen])

  if (!isOpen) return null

  const shortcuts = [
    { key: 'ESC', description: 'Close modals and dialogs' },
    { key: 'Enter', description: 'Submit forms (when focused)' },
    { key: 'Shift + ?', description: 'Show/hide keyboard shortcuts' },
  ]

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[70] animate-fade-in p-4"
      onClick={() => setIsOpen(false)}
    >
      <div 
        className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 animate-slide-in-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Keyboard Shortcuts</h2>
        </div>
        
        <div className="px-6 py-4">
          <div className="space-y-3">
            {shortcuts.map((shortcut, index) => (
              <div key={index} className="flex justify-between items-center">
                <span className="text-gray-700">{shortcut.description}</span>
                <kbd className="px-2 py-1 text-xs font-semibold text-gray-800 bg-gray-100 border border-gray-300 rounded">
                  {shortcut.key}
                </kbd>
              </div>
            ))}
          </div>
        </div>
        
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end">
          <button
            onClick={() => setIsOpen(false)}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

export default KeyboardShortcuts
