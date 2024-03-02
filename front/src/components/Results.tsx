interface ResultsProps {
  results: Record<string, Array<string>>;
}

export default function Results({ results }: ResultsProps) {
  // it would be cool to have it like google where it says how fast the query took.
  // it must be ≤ 300ms

  const resultsStrings = () => {
    if (JSON.stringify(results) == "{}") {
      return <p>Nothin' yet...</p>;
    }
    return results.urls.map((url, index) => (
      <div key={index}>
        <p>{url}</p>
      </div>
    ));
  };

  console.log(JSON.stringify(results) == "{}");
  return (
    <div>
      {resultsStrings()}
    </div>
  );
}
