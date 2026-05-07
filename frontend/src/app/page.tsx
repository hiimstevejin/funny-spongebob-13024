import Charts from "@/components/Charts";
import { getBaseUrl } from "@/lib/getBaseUrl";

// const data1 = [
//   { month: "Jan", mrr: 100 },
//   { month: "Feb", mrr: 50 },
//   { month: "Mar", mrr: 200 },
// ];

type MrrData = {
  month: string;
  mrr: number;
};

async function getMrrData(): Promise<MrrData[]> {
  const baseUrl = getBaseUrl();

  const res = await fetch(`${baseUrl}/api/mrr`, {
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error("Failed to fetch MRR data");
  }

  return res.json();
}

export default async function Home() {
  const data = await getMrrData();

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <Charts data={data} />
    </main>
  );
}
