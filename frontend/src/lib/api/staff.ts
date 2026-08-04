import { apiFetch } from "./client";

export interface StaffMember {
  id: number;
  name: string;
  platform_zone?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  is_available: boolean;
  last_acknowledged_at?: string | null;
}

export async function getStaff(): Promise<StaffMember[]> {
  return apiFetch<StaffMember[]>("/staff");
}

export async function getAvailableStaff(platformZone?: string): Promise<StaffMember[]> {
  const query = platformZone ? `?platform_zone=${encodeURIComponent(platformZone)}` : "";
  return apiFetch<StaffMember[]>(`/staff/available${query}`);
}

export async function createStaff(payload: {
  name: string;
  platform_zone?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
}): Promise<StaffMember> {
  return apiFetch<StaffMember>("/staff", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateStaffAvailability(
  id: number,
  isAvailable: boolean,
): Promise<StaffMember> {
  return apiFetch<StaffMember>(`/staff/${id}/availability`, {
    method: "PATCH",
    body: JSON.stringify({ is_available: isAvailable }),
  });
}
