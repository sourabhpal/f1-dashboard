import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { Button } from "@/components/ui/button";

export default function F1Dashboard() {
  const [raceData, setRaceData] = useState(null);
  const [year, setYear] = useState(2025);

  useEffect(() => {
    fetch(`/race/${year}/1`)
      .then((res) => res.json())
      .then((data) => setRaceData(data));
  }, [year]);

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">F1 Race Dashboard</h1>
      <Button onClick={() => setYear((prev) => prev - 1)}>Previous Year</Button>
      <Button onClick={() => setYear((prev) => prev + 1)}>Next Year</Button>
      {raceData && (
        <Card>
          <CardContent>
            <h2 className="text-xl font-semibold">{raceData.race_name}</h2>
            <p>{raceData.location} - {raceData.date}</p>
          </CardContent>
        </Card>
      )}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={[{ name: "Lap 1", time: 90 }, { name: "Lap 2", time: 88 }]}> 
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="time" stroke="#8884d8" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
