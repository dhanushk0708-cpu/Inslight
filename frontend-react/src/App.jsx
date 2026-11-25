import Sidebar from "./components/Sidebar/Sidebar";
import ResultsPanel from "./components/Dashboard/ResultsPanel";
import { useDashboardApp } from "./hooks/useDashboardApp";

export default function App() {
  const dashboard = useDashboardApp();

  return (
    <div className="app">
      <Sidebar dashboard={dashboard} />
      <ResultsPanel dashboard={dashboard} />
    </div>
  );
}
