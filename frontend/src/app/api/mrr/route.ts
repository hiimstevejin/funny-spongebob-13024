import { BigQuery } from "@google-cloud/bigquery";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

const projectId = process.env.GCP_PROJECT_ID;
const dataset = process.env.BQ_DATASET || "stripe_demo";

const bigquery = new BigQuery({
  projectId,
  credentials: {
    client_email: process.env.GOOGLE_CLOUD_CLIENT_EMAIL,
    private_key: process.env.GOOGLE_CLOUD_PRIVATE_KEY?.replace(/\\n/g, "\n"),
  },
});

export async function GET() {
  try {
    if (!projectId) {
      throw new Error("GCP_PROJECT_ID is not set");
    }

    const query = `
      WITH months AS (
        SELECT month_start
        FROM UNNEST(
          GENERATE_DATE_ARRAY(
            DATE '2025-11-01',
            DATE '2026-04-01',
            INTERVAL 1 MONTH
          )
        ) AS month_start
      ),

      month_ends AS (
        SELECT
          month_start,
          TIMESTAMP(DATETIME(LAST_DAY(month_start), TIME '23:59:59')) AS month_end_ts
        FROM months
      )

      SELECT
        FORMAT_DATE('%Y-%m', m.month_start) AS month,
        SUM(h.mrr_amount) / 100 AS mrr
      FROM month_ends m
      JOIN \`${projectId}.${dataset}.subscription_history\` h
        ON TIMESTAMP(h.valid_from) <= m.month_end_ts
        AND (
          h.valid_to IS NULL
          OR TIMESTAMP(h.valid_to) > m.month_end_ts
        )
      WHERE h.status IN ('active', 'past_due')
      GROUP BY month
      ORDER BY month;
    `;

    const [rows] = await bigquery.query({ query });

    return NextResponse.json(rows);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Failed to fetch MRR data:", message);

    return NextResponse.json(
      { error: "Failed to fetch MRR data", detail: message },
      { status: 500 },
    );
  }
}
