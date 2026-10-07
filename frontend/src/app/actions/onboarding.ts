"use server";

import { auth, clerkClient } from "@clerk/nextjs/server";
import { revalidatePath } from "next/cache";

export async function completeOnboarding(data: {
  currentRole: string;
  targetRole: string;
  timeline: string;
}) {
  const { userId } = await auth();
  
  if (!userId) {
    throw new Error("Unauthorized");
  }

  const client = await clerkClient();

  await client.users.updateUserMetadata(userId, {
    publicMetadata: {
      onboardingComplete: true,
      currentRole: data.currentRole,
      targetRole: data.targetRole,
      timeline: data.timeline,
    },
  });
  
  revalidatePath("/");
}
