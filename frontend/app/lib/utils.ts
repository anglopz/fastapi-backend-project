import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import type { Shipment } from "./client";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

function getLatestStatus(shipment: Shipment) {
  // Check if timeline exists and has items
  if (shipment.timeline && Array.isArray(shipment.timeline) && shipment.timeline.length > 0) {
    return shipment.timeline[shipment.timeline.length - 1].status
  }
  // Fallback to shipment status if timeline is not available
  return shipment.status || "unknown"
}

function getShipmentsCountWithStatus(
  shipments: Shipment[],
  status: string
) {
  if (!shipments || !Array.isArray(shipments)) {
    return 0
  }
  return shipments.filter((shipment) => getLatestStatus(shipment) === status).length;
}

export { cn, getLatestStatus, getShipmentsCountWithStatus as getShipmentsCountForStatus }