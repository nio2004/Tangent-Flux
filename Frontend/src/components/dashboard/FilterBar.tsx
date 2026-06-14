const filters = ["All Signals", "AI", "Research", "Architecture", "Pinned"];

interface FilterBarProps {
  activeFilter: string;
  onFilterChange: (filter: string) => void;
}

export function FilterBar({ activeFilter, onFilterChange }: FilterBarProps) {
  return (
    <div className="filter-bar" aria-label="Filter idea board">
      {filters.map((filter) => (
        <button
          key={filter}
          className={activeFilter === filter ? "filter-chip is-active" : "filter-chip"}
          type="button"
          onClick={() => onFilterChange(filter)}
        >
          {filter}
        </button>
      ))}
    </div>
  );
}
