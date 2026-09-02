# STEP 6: GIS Risk Map + Action & Alert System

## 1. GIS Architecture
The GIS engine (`/api/v1/gis/`) transforms the local risk calculations from STEP 5 into standardized RFC 7946 GeoJSON Feature Collections. It does not perform thermal or risk calculations itself; it strictly aggregates spatial boundaries and risk scores.

## 2. Boundary Sources
Real ward/zone polygons must be ingested via standard GIS formats (Shapefile/GeoJSON). Currently, boundaries are gracefully mocked: the system yields `geometry: null` and sets the `gis_data_status` property to `"BOUNDARIES_NOT_CONFIGURED"`. **We do not fabricate administrative ward boundaries.**

## 3. Geographic Hierarchy
The model maps data strictly across the following hierarchy:
`WARD` → `ZONE` → `CITY`

## 4. Spatial Joins & 5. Aggregation
Spatial joins rely on consistent `geographic_id` mapping. City or Zone-level aggregation computes a **population-weighted mean** of the constituent Wards' risk scores, allowing public safety officials to identify both the `highest-risk ward` and the generalized exposure level.

## 6. Risk-Map Schema
The API generates standard GeoJSON. Each `Feature` corresponds to a geographic unit. The `properties` dictionary exposes the full transparency breakdown: `risk_category`, `hazard_score`, `exposure_score`, `vulnerability_score`, `data_quality`. 

## 7. Action Engine & 8. Action Thresholds
The `ActionEngine` translates localized risk into municipal intervention recommendations. It utilizes an `EXPERT_HEURISTIC` mapping of Risk Categories to interventions. For example:
- `MODERATE`: "Prepare public messaging"
- `VERY_HIGH`: "Activate enhanced HAP, Open Cooling Centres"
- `EXTREME`: "Deploy emergency cooling, Restrict hazardous outdoor work"

## 9. Persistence Rules
Actions are conditionally scaled based on thermal persistence (e.g., duration of exposure). The forecast window spans up to 120 hours.

## 10. Alert Architecture
The engine generates actionable alerts (`AlertPayload`). It identifies events using an exact fingerprinting mechanism.

## 11. Provider Abstraction
The `NotificationService` relies on an interface (`NotificationProvider`). Mock `SMSProvider` and `WhatsAppProvider` are defined, demonstrating that the system is entirely provider-agnostic.

## 12. Notification Safety
By default, **`NOTIFICATION_ENABLED = False`**. 
- GET requests to the alert system (`/api/v1/alerts/current`) will *never* send notifications. 
- The Action Engine will generate alerts and set their lifecycle strictly to `PENDING`. 
- No API keys or secrets are stored in the codebase. 

## 13. Deduplication
Alerts are deduplicated against a strict SHA-256 fingerprint evaluating:
`(geographic_level, geographic_id, alert_category, forecast_start, forecast_end, rule_id)`.
If a new forecast evaluates to the same geographic unit and risk category for an overlapping period, it is suppressed. If the risk *category* escalates, the rule ID changes, generating a new escalated alert.

## 14. Alert Lifecycle
Alerts traverse through explicit states:
- **System Lifecycle**: `CREATED`, `PENDING`, `SENT`, `FAILED`
- **Municipal Action Status**: `RECOMMENDED`, `ACKNOWLEDGED`, `EXECUTED`. The system *never* infers `EXECUTED` automatically.

## 15. Data Quality
Risk map boundaries accurately report partial data or unavailable geometries without silently rendering 0 or drawing fake shapes.

## 16. Demo Mode
If `DEMO_DATA_ENABLED` is activated, synthetic profiles explicitly mark themselves as `is_real_data=False`, maintaining sandbox safety.

## 17. Limitations
- The system is a decision-support platform. It does not independently execute municipal actions.
- It does not provide medical diagnosis or mortality prediction.
- Real GIS ward boundary polygons and demographic distributions must be configured prior to production deployment.
