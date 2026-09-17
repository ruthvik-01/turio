import { Applications } from "@/components/applications";
export default async function Page({ searchParams }: { searchParams: Promise<{ outcome?: string }> }) {
  const { outcome } = await searchParams; return <Applications initialOutcome={outcome} />;
}
