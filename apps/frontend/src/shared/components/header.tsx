import { Link } from 'react-router-dom';

export function Header() {
  return (
    <header className="sticky top-0 z-50 bg-white border-b shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2">
            <img
              src="/logo-horizontal.png"
              alt="Universidad de Lima"
              className="h-8"
            />
            <span className="hidden sm:inline text-sm font-medium text-gray-600">
              Encuestas de Satisfacción
            </span>
          </Link>
          <nav className="flex items-center gap-4">
            <Link
              to="/"
              className="text-sm font-medium text-gray-600 hover:text-ulima-orange transition-colors"
            >
              Inicio
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
}
