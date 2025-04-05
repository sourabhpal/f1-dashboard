export function Button({ children, onClick, className }) {
    return (
      <button
        onClick={onClick}
        className={`px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition ${className}`}
      >
        {children}
      </button>
    );
  }