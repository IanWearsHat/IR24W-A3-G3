import "./Results.css";

interface ResultsProps {
  results: Record<string, Array<string> | number>;
}

export default function Results({ results }: ResultsProps) {
  // it would be cool to have it like google where it says how fast the query took.
  // it must be ≤ 300ms

  const resultsStrings = () => {
    if (JSON.stringify(results) == "{}") {
      return <p>Nothin'. No results yet...</p>;
    }
    return (
      <>
        {typeof results.time === "number" && (
          <p style={{ marginBottom: "3em" }}>
            {(1000 * results.time).toFixed(6)} ms taken
          </p>
        )}
        {Array.isArray(results.urls) && results.urls.length == 0 && (
          <p>No relevant documents found</p>
        )}
        {Array.isArray(results.urls) &&
          results.urls.map((url, index) => (
            <div key={index}>
              <p>
                {index + 1}.{" "}
                <span style={{ color: "rgb(26, 98, 192)" }}>{url}</span>
              </p>
            </div>
          ))}
      </>
    );
  };

  return <div className="results">{resultsStrings()}</div>;
}
