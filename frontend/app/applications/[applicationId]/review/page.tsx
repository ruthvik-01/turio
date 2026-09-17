import { ApplicationDetail } from "@/components/applications";
export default async function Page({ params }: { params: Promise<{ applicationId: string }> }) {
  const { applicationId } = await params; return <ApplicationDetail applicationId={applicationId} reviewMode />;
}
