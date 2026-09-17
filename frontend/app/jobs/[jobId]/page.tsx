import { JobDetail } from "@/components/jobs";
export default async function Page({ params, searchParams }: { params: Promise<{ jobId: string }>; searchParams: Promise<{ match?: string }> }) {
  const { jobId } = await params; const { match } = await searchParams;
  return <JobDetail jobId={jobId} matchId={match} />;
}
