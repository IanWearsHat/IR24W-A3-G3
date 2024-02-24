interface ResultsProps {
  results: string;
}

export default function Results({ results }: ResultsProps) {
  // it would be cool to have it like google where it says how fast the query took.
  // it must be ≤ 300ms
  return (
    <div>
      (results ? <p>{results}</p> : <p>Nothin' yet...</p>)
    </div>
  );
}
