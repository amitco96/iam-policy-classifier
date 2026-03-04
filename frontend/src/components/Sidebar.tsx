import { NavLink } from 'react-router-dom';

const navItems = [
  { to: '/', label: 'Classify' },
  { to: '/batch', label: 'Batch' },
  { to: '/history', label: 'History' },
];

export default function Sidebar() {
  return (
    <aside className="w-60 shrink-0 h-screen sticky top-0 bg-white border-r border-gray-200 flex flex-col">
      {/* Shield icon */}
      <div className="flex items-center justify-center h-16 border-b border-gray-200">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="w-8 h-8 text-indigo-600"
          aria-label="IAM Policy Classifier"
        >
          <path
            fillRule="evenodd"
            d="M12 1.5a5.25 5.25 0 0 0-5.25 5.25v3a3 3 0 0 0-3 3v6.75a3 3 0 0 0 3 3h10.5a3 3 0 0 0 3-3v-6.75a3 3 0 0 0-3-3v-3c0-2.9-2.35-5.25-5.25-5.25Zm3.75 8.25v-3a3.75 3.75 0 1 0-7.5 0v3h7.5Z"
            clipRule="evenodd"
          />
        </svg>
      </div>

      {/* Navigation */}
      <nav className="flex flex-col gap-1 p-3 flex-1">
        {navItems.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              [
                'flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors',
                isActive
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
              ].join(' ')
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
