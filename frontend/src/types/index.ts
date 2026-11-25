export interface User {
  id: string;
  name: string;
  email: string;
  role?: "admin" | "analyst" | string;
  is_active: boolean;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ColumnInfo {
  name: string;
  dtype: string;
  semantic_type: string;
  unique_count: number;
  sample_values: string[];
  null_count: number;
  stats?: {
    mean: number;
    min: number;
    max: number;
  };
}

export interface DatasetProfile {
  id?: string;
  filename: string;
  rows: number;
  columns: number;
  column_info: ColumnInfo[];
  data_quality_score: number;
  missing_values: Record<string, number>;
  suggested_questions: string[];
  preview: Array<Record<string, any>>;
}

export interface Dataset {
  id: string;
  user_id: string;
  original_filename: string;
  table_name: string;
  row_count: number;
  column_count: number;
  created_at?: string;
  columns?: string[];
  profile?: DatasetProfile;
}

export interface KPICard {
  label: string;
  value: string;
  trend?: string | null;
  trend_direction?: "up" | "down" | "neutral";
}

export interface ChartConfig {
  type: string;
  title: string;
  x_axis: string;
  y_axis: string;
  data: Array<Record<string, any>>;
  series?: any;
  highlight?: any;
}

export interface OpportunityItem {
  rank: number;
  title: string;
  is_hypothesis?: boolean;
  supporting_metric?: string;
  actual_value?: string;
  evidence_source?: string;
  business_interpretation?: string;
  impact: string;
  recommendation: string;
}

export interface RiskItem {
  rank: number;
  title: string;
  severity: "critical" | "warning" | "info" | string;
  supporting_metric?: string;
  actual_value?: string;
  evidence_source?: string;
  business_interpretation?: string;
  impact: string;
  mitigation: string;
}

export interface QueryResult {
  kpi_cards: KPICard[];
  main_chart?: ChartConfig | null;
  secondary_chart?: ChartConfig | null;
  narrative: string;
  summary?: string | null;
  opportunities?: OpportunityItem[];
  risks?: RiskItem[];
  supporting_table?: {
    title?: string;
    columns: string[];
    rows: Array<Record<string, any>>;
  } | null;
  analytical_steps?: string[];
  suggested_followups: string[];
  sql_query?: string | null;
  error?: string | null;
  suggestion?: string | null;
  available_columns?: string[];
  data_quality?: any;
  session_id?: string | null;
}

export interface WhatIfData {
  current: { revenue: number; units: number };
  projected: { revenue: number };
  change: { revenue_diff: number; revenue_pct_change: number };
  monthly_comparison: Array<{ month: string; actual_revenue: number; projected_revenue: number }>;
  category_impact: Array<{ category: string; current_revenue: number; projected_revenue: number; change_pct: number }>;
  ai_commentary: string;
  error?: string | null;
}

export interface DeepDiveData {
  top_revenue_drivers: Array<{ name: string; revenue: number; trend: string }>;
  risk_areas: Array<{ name: string; issue: string; impact_amount: number; severity: string }>;
  root_cause_analysis: string;
  recommendations: Array<{ action: string; expected_impact: string; priority: string }>;
  monthly_trend?: Array<{ month: string; total_revenue: number; total_profit?: number; margin_pct?: number | null }>;
  revenue_by_category?: Array<{ product_category: string; total_revenue: number }>;
  error?: string | null;
  // Comprehensive 10-Section Research Workspace fields
  dataset_metadata?: {
    dataset_id: string;
    filename: string;
    row_count: number;
    column_count: number;
    columns: string[];
    numeric_metrics: string[];
    categorical_dimensions: string[];
    date_coverage?: { start: string; end: string; date_column: string } | null;
    data_quality_score: number;
    issues_count: number;
    available_analyses: string[];
    limitations: string[];
  };
  executive_summary?: {
    health_summary: string;
    kpi_cards: KPICard[];
    key_findings: string[];
    warnings: string[];
  };
  revenue_analysis?: any;
  profitability_analysis?: any;
  product_analysis?: any;
  category_analysis?: any;
  regional_analysis?: any;
  customer_analysis?: any;
  trend_and_forecast?: any;
  anomalies_and_risks?: any;
  opportunities?: OpportunityItem[];
  strategic_action_plan?: {
    short_term?: Array<any>;
    medium_term?: Array<any>;
  };
  charts?: Record<string, ChartConfig & { interpretation?: string }>;
  execution_stages?: string[];
}

export interface AnomalyItem {
  metric: string;
  description: string;
  severity: "high" | "medium" | "low";
  suggestion: string;
}

export interface AnomalyData {
  anomalies: string[];
  count: number;
  ai_analysis: AnomalyItem[];
  error?: string | null;
}

export interface ChatMessage {
  role: "user" | "ai";
  text: string;
  time: string;
  suggestions?: string[];
}

export interface ReportItem {
  id: string;
  user_id: string;
  dataset_id?: string | null;
  name: string;
  report_format: "pdf" | "excel" | "csv";
  file_size: number;
  recipients?: string | null;
  email_subject?: string | null;
  status: "generated" | "sent" | "failed";
  gmail_message_id?: string | null;
  created_at: string;
}

export interface ScheduledReportItem {
  id: string;
  user_id: string;
  dataset_id: string;
  report_name: string;
  frequency: "weekly" | "monthly";
  report_format: "pdf" | "excel" | "both";
  recipients: string;
  email_subject: string;
  email_body: string;
  is_active: boolean;
  next_run_at: string;
  last_run_at?: string | null;
  last_status?: string | null;
  created_at: string;
}

export interface GmailStatus {
  is_connected: boolean;
  email?: string | null;
  provider: string;
}

export type VoiceLanguage = "en-IN" | "hi-IN" | "kn-IN";

// ━━━━━━━━ PHASE 3: ADVANCED AI BI TYPES ━━━━━━━━

export interface RootCauseData {
  status: string;
  metric: string;
  period_label: string;
  baseline_value: number;
  current_value: number;
  absolute_change: number;
  percentage_change: number;
  direction: "increase" | "decline";
  formatted_baseline: string;
  formatted_current: string;
  formatted_change: string;
  top_contributors: Array<{
    dimension: string;
    segment: string;
    baseline_val: number;
    current_val: number;
    delta: number;
    contribution_pct: number;
    formatted_delta: string;
  }>;
  price_volume_decomposition?: {
    volume_effect: number;
    volume_effect_share_pct: number;
    price_effect: number;
    price_effect_share_pct: number;
    baseline_asp: number;
    current_asp: number;
    baseline_volume: number;
    current_volume: number;
    primary_driver: string;
  } | null;
  hypotheses: Array<{
    factor: string;
    evidence: string;
    relationship: string;
    confidence: "HIGH" | "MEDIUM" | "LOW";
  }>;
  recommended_investigations: string[];
  message?: string;
}

export interface ForecastData {
  status: string;
  metric: string;
  method_used: string;
  horizon_label: string;
  horizon_steps: number;
  granularity: string;
  evaluation_metrics?: {
    mae: number;
    rmse: number;
    mape_pct: number;
  };
  historical_total: number;
  forecasted_total: number;
  mean_period_forecast: number;
  trend_direction: string;
  projected_growth_pct: number;
  formatted_forecast_total: string;
  history_data: Array<{
    date: string;
    actual: number | null;
    predicted: number | null;
    lower_bound: number | null;
    upper_bound: number | null;
  }>;
  forecast_data: Array<{
    date: string;
    actual: number | null;
    predicted: number | null;
    lower_bound: number | null;
    upper_bound: number | null;
  }>;
  limitations: string;
  message?: string;
}

export interface AdvancedAnomalyData {
  status: string;
  total_records_scanned: number;
  anomalies_detected_count: number;
  risks_count: number;
  opportunities_count: number;
  anomalies: Array<{
    id: string;
    metric: string;
    observed_value: number;
    baseline: number;
    deviation_pct: number;
    severity: "HIGH" | "MEDIUM" | "LOW";
    detection_method: string;
    type: "opportunity" | "risk";
    segment: string;
    summary: string;
    business_significance: string;
  }>;
  governance_note: string;
  message?: string;
}

export interface BusinessAlert {
  id: string;
  user_id: string;
  dataset_id?: string | null;
  title: string;
  category: string;
  severity: string;
  description: string;
  evidence_json?: string | null;
  metric_name?: string | null;
  observed_value?: number | null;
  threshold_value?: number | null;
  is_read: boolean;
  is_resolved: boolean;
  created_at: string;
}

export interface AlertRuleItem {
  id: string;
  user_id: string;
  dataset_id?: string | null;
  name: string;
  metric_name: string;
  condition: string;
  threshold_value: number;
  category: string;
  severity: string;
  is_active: boolean;
  created_at: string;
}

export interface DataQualityReport {
  status: string;
  overall_score: number;
  quality_grade: string;
  total_records_analyzed: number;
  total_columns_analyzed: number;
  issues_count: number;
  issues: Array<{
    column: string;
    issue_type: string;
    affected_records: number;
    affected_pct?: number;
    example_values?: string;
    severity: string;
    recommendation: string;
  }>;
  cleaning_actions: Array<{
    id: string;
    title: string;
    description: string;
    impact: string;
  }>;
  governance_summary: string;
}

export interface ComparisonData {
  status: string;
  comparison_type: string;
  metric: string;
  latest_comparison?: {
    period_label: string;
    current_period: string;
    baseline_period: string;
    current_value: number;
    baseline_value: number;
    absolute_difference: number;
    percentage_change: number;
    formatted_change: string;
    trend: string;
  };
  timeline?: Array<{
    period_label: string;
    current_period: string;
    baseline_period: string;
    current_value: number;
    baseline_value: number;
    absolute_difference: number;
    percentage_change: number;
    formatted_change: string;
    trend: string;
  }>;
  segment_a?: { name: string; value: number; transactions: number };
  segment_b?: { name: string; value: number; transactions: number };
  absolute_difference?: number;
  percentage_difference?: number;
  formatted_difference?: string;
  message?: string;
}

export interface SavedDashboardItem {
  id: string;
  user_id: string;
  dataset_id?: string | null;
  title: string;
  description?: string | null;
  layout_config: string;
  is_favorite: boolean;
  created_at: string;
  updated_at: string;
}

export interface DatasetRelationshipItem {
  id: string;
  user_id: string;
  source_dataset_id: string;
  target_dataset_id: string;
  source_column: string;
  target_column: string;
  relationship_type: string;
  cardinality_status: string;
  source_dataset_name?: string | null;
  target_dataset_name?: string | null;
  created_at: string;
}

export interface RelationshipCandidateItem {
  source_column: string;
  target_column: string;
  match_type: string;
}

export interface RelationshipValidationStats {
  total_rows: number;
  null_keys: number;
  distinct_keys: number;
  is_unique: boolean;
}

export interface RelationshipValidationResult {
  is_valid: boolean;
  source_column: string;
  target_column: string;
  cardinality: string;
  risk_level: string;
  warnings: string[];
  source_stats: RelationshipValidationStats;
  target_stats: RelationshipValidationStats;
}

export interface RelationshipPreviewResult {
  status: string;
  columns: string[];
  records: Array<Record<string, any>>;
  total_preview_count: number;
  message?: string;
}

export interface NotificationItem {
  id: string;
  user_id: string;
  category: string;
  title: string;
  message: string;
  is_read: boolean;
  resource_type?: string | null;
  resource_id?: string | null;
  created_at: string;
}

export interface AuditLogItem {
  id: string;
  user_id?: string | null;
  action: string;
  resource_type: string;
  resource_id?: string | null;
  status: string;
  request_id?: string | null;
  metadata_json?: string | null;
  created_at: string;
}

export interface SlideOutlineItem {
  slide_number: number;
  title: string;
  layout: string;
  bullets: string[];
  metric_highlight?: string | null;
  notes?: string | null;
}

export interface PresentationOutline {
  status: string;
  dataset_id: string;
  dataset_name: string;
  title: string;
  presentation_type: string;
  slides: SlideOutlineItem[];
}

export interface PresentationItem {
  id: string;
  user_id: string;
  dataset_id?: string | null;
  title: string;
  presentation_type: string;
  slide_count: number;
  created_at: string;
}
