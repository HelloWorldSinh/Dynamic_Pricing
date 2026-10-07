import React, { useState, useEffect, useId } from 'react';
import { MatrixSimulationRequest, MatrixSimulationResponse } from '../types/pricing';
import { simulateMatrixPricingApi } from '../api/pricingApi';
import { formatCurrencyVND, formatPercent } from '../utils/formatters';

interface ScenarioPreset {
  id: string;
  name: string;
  description: string;
  d: number;
  i: number;
  c: number;
}

const PRESET_SCENARIOS: ScenarioPreset[] = [
  {
    id: 's1',
    name: 'Kịch bản 1: Festival / Sự kiện lớn',
    description: 'Nhu cầu bùng nổ (+2), hàng khan hiếm (+2), đối thủ giá cao (+2)',
    d: 2.0,
    i: 2.0,
    c: 2.0,
  },
  {
    id: 's2',
    name: 'Kịch bản 2: Sản phẩm Viral',
    description: 'Lượt tìm kiếm tăng vọt (+2), kho bình thường (0), đối thủ chưa đổi (0)',
    d: 2.0,
    i: 0.0,
    c: 0.0,
  },
  {
    id: 's3',
    name: 'Kịch bản 3: Bình thường (Baseline)',
    description: 'Thị trường cân bằng, cung cầu ổn định (D=0, I=0, C=0)',
    d: 0.0,
    i: 0.0,
    c: 0.0,
  },
  {
    id: 's4',
    name: 'Kịch bản 4: Cầu cao nhưng Hàng ứ',
    description: 'Nhu cầu cao (+2) nhưng tồn kho quá lớn (-2), đối thủ ngang (0)',
    d: 2.0,
    i: -2.0,
    c: 0.0,
  },
  {
    id: 's5',
    name: 'Kịch bản 5: Hàng khan, Đối thủ hết nhưng Cầu yếu',
    description: 'Kho sắp hết (+2), đối thủ hết hàng (+2), nhưng cầu thấp (-1)',
    d: -1.0,
    i: 2.0,
    c: 2.0,
  },
  {
    id: 's6',
    name: 'Kịch bản 6: Khủng hoảng Nhu cầu',
    description: 'Cả 3 yếu tố chạm đáy: cầu giảm (-2), kho ứ (-2), đối thủ phá giá (-2)',
    d: -2.0,
    i: -2.0,
    c: -2.0,
  },
  {
    id: 's7',
    name: 'Kịch bản 7: Khách quay lưng, Đối thủ rẻ',
    description: 'Cầu sụt giảm (-2), kho bình thường (0), đối thủ bán rẻ (-2)',
    d: -2.0,
    i: 0.0,
    c: -2.0,
  },
  {
    id: 's8',
    name: 'Kịch bản 8: Cầu cao, Hàng khan nhưng Đối thủ rẻ',
    description: 'Nhu cầu cao (+2), kho khan (+2), đối thủ rẻ (-2)',
    d: 2.0,
    i: 2.0,
    c: -2.0,
  },
  {
    id: 's9',
    name: 'Kịch bản 9: Tín hiệu Hỗn độn',
    description: 'Các tín hiệu ngược chiều nhau (D=+1, I=-1, C=+1)',
    d: 1.0,
    i: -1.0,
    c: 1.0,
  },
  {
    id: 's10',
    name: 'Đặc biệt: Cuối vòng đời (Clearance)',
    description: 'Sản phẩm lỗi thời EOL, xả kho thu hồi vốn (D=-2, I=-2, C=0)',
    d: -2.0,
    i: -2.0,
    c: 0.0,
  },
];

interface WeightPreset {
  id: string;
  name: string;
  weights: { D: number; I: number; C: number };
}

const WEIGHT_PRESETS: WeightPreset[] = [
  {
    id: 'standard',
    name: 'Mặc định ICT (D: 40% - I: 35% - C: 25%)',
    weights: { D: 0.40, I: 0.35, C: 0.25 },
  },
  {
    id: 'fmcg',
    name: 'FMCG / Phụ kiện (D: 45% - I: 30% - C: 25%)',
    weights: { D: 0.45, I: 0.30, C: 0.25 },
  },
  {
    id: 'flagship',
    name: 'Hàng khan hiếm / Flagship (D: 35% - I: 45% - C: 20%)',
    weights: { D: 0.35, I: 0.45, C: 0.20 },
  },
  {
    id: 'commodity',
    name: 'Hàng phổ thông / Laptop VP (D: 30% - I: 40% - C: 30%)',
    weights: { D: 0.30, I: 0.40, C: 0.30 },
  },
];

export const MatrixSimulatorPage: React.FC = () => {
  const scenarioSelectId = useId();
  const weightSelectId = useId();
  const currentPriceId = useId();
  const costPriceId = useId();
  const floorPriceId = useId();
  const competitorPriceId = useId();
  const rateCapId = useId();

  // Inputs
  const [selectedPresetId, setSelectedPresetId] = useState<string>('s1');
  const [demandScore, setDemandScore] = useState<number>(2.0);
  const [inventoryScore, setInventoryScore] = useState<number>(2.0);
  const [competitorScore, setCompetitorScore] = useState<number>(2.0);

  const [weightPresetId, setWeightPresetId] = useState<string>('standard');
  const [weightD, setWeightD] = useState<number>(0.40);
  const [weightI, setWeightI] = useState<number>(0.35);
  const [weightC, setWeightC] = useState<number>(0.25);

  const [currentPrice, setCurrentPrice] = useState<number>(25000000);
  const [costPrice, setCostPrice] = useState<number>(20000000);
  const [floorPrice, setFloorPrice] = useState<number>(21000000);
  const [competitorPrice, setCompetitorPrice] = useState<number>(26000000);
  const [maxRateCap, setMaxRateCap] = useState<number>(0.10);

  // Results
  const [simulationResult, setSimulationResult] = useState<MatrixSimulationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Handle Preset Selection
  const handleSelectPreset = (presetId: string) => {
    setSelectedPresetId(presetId);
    if (presetId === 'custom') return;
    const found = PRESET_SCENARIOS.find((p) => p.id === presetId);
    if (found) {
      setDemandScore(found.d);
      setInventoryScore(found.i);
      setCompetitorScore(found.c);
    }
  };

  // Handle Weight Preset Selection
  const handleSelectWeightPreset = (presetId: string) => {
    setWeightPresetId(presetId);
    if (presetId === 'custom_weight') return;
    const found = WEIGHT_PRESETS.find((w) => w.id === presetId);
    if (found) {
      setWeightD(found.weights.D);
      setWeightI(found.weights.I);
      setWeightC(found.weights.C);
    }
  };

  // Run simulation
  const runSimulation = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const payload: MatrixSimulationRequest = {
        demand_score: demandScore,
        inventory_score: inventoryScore,
        competitor_score: competitorScore,
        weights: {
          D: weightD,
          I: weightI,
          C: weightC,
        },
        current_price: currentPrice,
        cost_price: costPrice,
        floor_price: floorPrice,
        competitor_price: competitorPrice > 0 ? competitorPrice : undefined,
        max_rate_cap: maxRateCap,
      };

      const res = await simulateMatrixPricingApi(payload);
      setSimulationResult(res);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Lỗi không xác định khi mô phỏng';
      setErrorMsg(message);
    } finally {
      setLoading(false);
    }
  };

  // Run once on mount and when signals change
  useEffect(() => {
    runSimulation();
  }, [
    demandScore,
    inventoryScore,
    competitorScore,
    weightD,
    weightI,
    weightC,
    currentPrice,
    costPrice,
    floorPrice,
    competitorPrice,
    maxRateCap,
  ]);

  // Styling helpers
  const getActionTypeClass = (actionType: string) => {
    const act = actionType.toLowerCase();
    if (act.includes('strong raise')) {
      return 'bg-emerald-50 text-emerald-800 border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800';
    }
    if (act.includes('moderate raise')) {
      return 'bg-teal-50 text-teal-800 border-teal-300 dark:bg-teal-950/40 dark:text-teal-300 dark:border-teal-800';
    }
    if (act.includes('mild raise')) {
      return 'bg-cyan-50 text-cyan-800 border-cyan-300 dark:bg-cyan-950/40 dark:text-cyan-300 dark:border-cyan-800';
    }
    if (act.includes('hold')) {
      return 'bg-slate-100 text-slate-800 border-slate-300 dark:bg-slate-800 dark:text-slate-200 dark:border-slate-700';
    }
    if (act.includes('mild lower')) {
      return 'bg-amber-50 text-amber-800 border-amber-300 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800';
    }
    if (act.includes('moderate lower')) {
      return 'bg-orange-50 text-orange-800 border-orange-300 dark:bg-orange-950/40 dark:text-orange-300 dark:border-orange-800';
    }
    if (act.includes('strong lower') || act.includes('clearance')) {
      return 'bg-rose-50 text-rose-800 border-rose-300 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800';
    }
    return 'bg-slate-100 text-slate-800 border-slate-300 dark:bg-slate-800 dark:text-slate-200 dark:border-slate-700';
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">
              Phòng Thử Nghiệm Ma Trận Định Giá (Pricing Matrix Sandbox)
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Kiểm thử tương tác trực tiếp 9 kịch bản nghiệp vụ chuẩn, 7 dải Composite Score và rào cản an toàn Guardrails.
            </p>
          </div>
          <button
            onClick={runSimulation}
            disabled={loading}
            className="px-4 py-2 bg-orange-600 hover:bg-orange-700 disabled:opacity-50 text-white text-xs font-semibold rounded-lg transition shadow-sm text-center"
          >
            {loading ? 'Đang tính toán...' : 'Tính toán lại'}
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800">
          Lỗi: {errorMsg}
        </div>
      )}

      {/* Main Grid: Controls vs Results */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Simulation Controls (7 cols) */}
        <div className="lg:col-span-7 space-y-5">
          {/* Section 1: Scenario Presets */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white uppercase tracking-wider text-[11px]">
              1. Chọn Kịch Bản Mẫu Nghiệp Vụ
            </h3>
            <div>
              <label htmlFor={scenarioSelectId} className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                Kịch bản định giá (Scenario Preset)
              </label>
              <select
                id={scenarioSelectId}
                value={selectedPresetId}
                onChange={(e) => handleSelectPreset(e.target.value)}
                className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-orange-500"
              >
                <option value="custom">Tuỳ biến tham số thủ công</option>
                {PRESET_SCENARIOS.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
              {selectedPresetId !== 'custom' && (
                <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1.5 italic">
                  {PRESET_SCENARIOS.find((p) => p.id === selectedPresetId)?.description}
                </p>
              )}
            </div>
          </div>

          {/* Section 2: Market Signals Sliders */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white uppercase tracking-wider text-[11px]">
              2. Điểm Số Tín Hiệu Thị Trường (-2.0 đến +2.0)
            </h3>

            {/* Demand Slider */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center text-xs">
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  Nhu cầu thị trường (Demand Score - D)
                </span>
                <span className="font-mono font-bold text-slate-900 dark:text-white">
                  {demandScore > 0 ? `+${demandScore.toFixed(1)}` : demandScore.toFixed(1)}
                </span>
              </div>
              <input
                type="range"
                min="-2.0"
                max="2.0"
                step="0.5"
                value={demandScore}
                onChange={(e) => {
                  setDemandScore(parseFloat(e.target.value));
                  setSelectedPresetId('custom');
                }}
                className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-orange-600"
              />
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>-2.0 (Cầu chạm đáy)</span>
                <span>0.0 (Bình thường)</span>
                <span>+2.0 (Bùng nổ)</span>
              </div>
            </div>

            {/* Inventory Slider */}
            <div className="space-y-1.5 pt-2">
              <div className="flex justify-between items-center text-xs">
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  Tồn kho & DOH (Inventory Score - I)
                </span>
                <span className="font-mono font-bold text-slate-900 dark:text-white">
                  {inventoryScore > 0 ? `+${inventoryScore.toFixed(1)}` : inventoryScore.toFixed(1)}
                </span>
              </div>
              <input
                type="range"
                min="-2.0"
                max="2.0"
                step="0.5"
                value={inventoryScore}
                onChange={(e) => {
                  setInventoryScore(parseFloat(e.target.value));
                  setSelectedPresetId('custom');
                }}
                className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-orange-600"
              />
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>-2.0 (Ứ đọng nặng)</span>
                <span>0.0 (Đủ tồn kho)</span>
                <span>+2.0 (Khan hiếm)</span>
              </div>
            </div>

            {/* Competitor Slider */}
            <div className="space-y-1.5 pt-2">
              <div className="flex justify-between items-center text-xs">
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  Phản ứng đối thủ (Competitor Score - C)
                </span>
                <span className="font-mono font-bold text-slate-900 dark:text-white">
                  {competitorScore > 0 ? `+${competitorScore.toFixed(1)}` : competitorScore.toFixed(1)}
                </span>
              </div>
              <input
                type="range"
                min="-2.0"
                max="2.0"
                step="0.5"
                value={competitorScore}
                onChange={(e) => {
                  setCompetitorScore(parseFloat(e.target.value));
                  setSelectedPresetId('custom');
                }}
                className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-orange-600"
              />
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>-2.0 (Đối thủ rẻ hơn)</span>
                <span>0.0 (Ngang bằng)</span>
                <span>+2.0 (Đối thủ đắt/hết hàng)</span>
              </div>
            </div>
          </div>

          {/* Section 3: Category Weights & Financials */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white uppercase tracking-wider text-[11px]">
              3. Trọng Số Ngành Hàng & Thông Số Tài Chính
            </h3>

            {/* Weights Preset */}
            <div>
              <label htmlFor={weightSelectId} className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                Nhóm ngành hàng (Weight Profile)
              </label>
              <select
                id={weightSelectId}
                value={weightPresetId}
                onChange={(e) => handleSelectWeightPreset(e.target.value)}
                className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-orange-500"
              >
                {WEIGHT_PRESETS.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.name}
                  </option>
                ))}
                <option value="custom_weight">Tự cấu hình tỷ lệ trọng số</option>
              </select>
            </div>

            {/* Financial Input Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div>
                <label htmlFor={currentPriceId} className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Giá FPT hiện tại (VND)
                </label>
                <input
                  id={currentPriceId}
                  type="number"
                  step="500000"
                  value={currentPrice}
                  onChange={(e) => setCurrentPrice(Math.max(1, parseInt(e.target.value) || 0))}
                  className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-orange-500 font-mono"
                />
              </div>

              <div>
                <label htmlFor={costPriceId} className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Giá vốn nhập kho Cost (VND)
                </label>
                <input
                  id={costPriceId}
                  type="number"
                  step="500000"
                  value={costPrice}
                  onChange={(e) => setCostPrice(Math.max(0, parseInt(e.target.value) || 0))}
                  className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-orange-500 font-mono"
                />
              </div>

              <div>
                <label htmlFor={floorPriceId} className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Giá sàn tối thiểu Floor (VND)
                </label>
                <input
                  id={floorPriceId}
                  type="number"
                  step="500000"
                  value={floorPrice}
                  onChange={(e) => setFloorPrice(Math.max(0, parseInt(e.target.value) || 0))}
                  className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-orange-500 font-mono"
                />
              </div>

              <div>
                <label htmlFor={competitorPriceId} className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Giá đối thủ cạnh tranh (VND)
                </label>
                <input
                  id={competitorPriceId}
                  type="number"
                  step="500000"
                  value={competitorPrice}
                  onChange={(e) => setCompetitorPrice(Math.max(0, parseInt(e.target.value) || 0))}
                  className="w-full text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-orange-500 font-mono"
                />
              </div>
            </div>

            {/* Rate Cap Slider */}
            <div className="pt-2">
              <div className="flex justify-between items-center text-xs mb-1">
                <label htmlFor={rateCapId} className="font-medium text-slate-700 dark:text-slate-300">
                  Trần biên độ hãm sốc giá (Rate-of-Change Cap)
                </label>
                <span className="font-mono font-bold text-slate-900 dark:text-white">
                  {(maxRateCap * 100).toFixed(0)}%
                </span>
              </div>
              <input
                id={rateCapId}
                type="range"
                min="0.05"
                max="0.25"
                step="0.01"
                value={maxRateCap}
                onChange={(e) => setMaxRateCap(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-orange-600"
              />
            </div>
          </div>
        </div>

        {/* Right Column: Real-time Evaluation Results (5 cols) */}
        <div className="lg:col-span-5 space-y-5">
          {simulationResult ? (
            <>
              {/* Output Summary Card */}
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    Kết Quả Đề Xuất
                  </span>
                  <span
                    className={`px-2.5 py-1 text-xs font-bold rounded-md border ${getActionTypeClass(
                      simulationResult.action_type
                    )}`}
                  >
                    {simulationResult.action_type}
                  </span>
                </div>

                {/* Scenario Name */}
                <div>
                  <span className="text-[11px] text-slate-400 block mb-0.5">Kịch bản nhận diện</span>
                  <p className="text-sm font-bold text-slate-900 dark:text-white">
                    {simulationResult.scenario_name}
                  </p>
                </div>

                {/* Composite Score Meter */}
                <div className="bg-slate-50 dark:bg-slate-800/60 p-3.5 rounded-lg border border-slate-100 dark:border-slate-800 space-y-1.5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-500 dark:text-slate-400">Điểm tổng hợp Composite Score</span>
                    <span className="font-mono font-black text-sm text-slate-900 dark:text-white">
                      {simulationResult.composite_score > 0
                        ? `+${simulationResult.composite_score.toFixed(2)}`
                        : simulationResult.composite_score.toFixed(2)}
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-400 font-mono">
                    Công thức: {demandScore} x {weightD} + {inventoryScore} x {weightI} + {competitorScore} x {weightC}
                  </div>
                </div>

                {/* Recommended Price Display */}
                <div className="p-4 bg-orange-500/5 border border-orange-500/20 rounded-xl space-y-2">
                  <span className="text-[11px] font-medium text-orange-600 dark:text-orange-400 block">
                    Giá đề xuất điều chỉnh (Final Recommended Price)
                  </span>
                  <div className="flex items-baseline justify-between">
                    <span className="text-2xl font-black font-mono text-slate-900 dark:text-white">
                      {formatCurrencyVND(simulationResult.recommended_price)}
                    </span>
                    <span
                      className={`text-sm font-bold font-mono ${
                        simulationResult.price_delta_pct > 0
                          ? 'text-emerald-600 dark:text-emerald-400'
                          : simulationResult.price_delta_pct < 0
                          ? 'text-rose-600 dark:text-rose-400'
                          : 'text-slate-500'
                      }`}
                    >
                      {formatPercent(simulationResult.price_delta_pct * 100)}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400 pt-1 border-t border-orange-500/10 font-mono">
                    <span>Chênh lệch: {formatCurrencyVND(simulationResult.price_delta_amount)}</span>
                    <span>Mục tiêu ma trận: {formatPercent(simulationResult.target_delta_pct * 100)}</span>
                  </div>
                </div>

                {/* Guardrail Status Flags */}
                <div className="space-y-2 pt-1">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                    Trạng Thái Rào Cản An Toàn (Guardrails)
                  </span>

                  <div className="flex flex-col gap-2 text-xs">
                    {/* Floor protection badge */}
                    <div className="flex items-center justify-between p-2.5 rounded-lg border bg-slate-50 dark:bg-slate-800/40 border-slate-200 dark:border-slate-800">
                      <span className="text-slate-700 dark:text-slate-300">Bảo vệ giá sàn (Margin Floor)</span>
                      {simulationResult.is_floor_capped ? (
                        <span className="px-2 py-0.5 text-[11px] font-bold rounded bg-rose-100 text-rose-800 border border-rose-300 dark:bg-rose-950/60 dark:text-rose-300 dark:border-rose-800">
                          Đã chặn tại giá sàn
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 text-[11px] font-medium rounded bg-emerald-100 text-emerald-800 border border-emerald-300 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800">
                          An toàn
                        </span>
                      )}
                    </div>

                    {/* Rate Cap badge */}
                    <div className="flex items-center justify-between p-2.5 rounded-lg border bg-slate-50 dark:bg-slate-800/40 border-slate-200 dark:border-slate-800">
                      <span className="text-slate-700 dark:text-slate-300">Trần bước nhảy (Rate Cap)</span>
                      {Math.abs(simulationResult.target_delta_pct) > maxRateCap ? (
                        <span className="px-2 py-0.5 text-[11px] font-bold rounded bg-amber-100 text-amber-800 border border-amber-300 dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-800">
                          Đã hãm trần {(maxRateCap * 100).toFixed(0)}%
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 text-[11px] font-medium rounded bg-emerald-100 text-emerald-800 border border-emerald-300 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800">
                          Trong biên độ an toàn
                        </span>
                      )}
                    </div>

                    {/* Predatory Check */}
                    {competitorPrice > 0 && costPrice > 0 && competitorPrice < Math.round(costPrice * 0.8) && (
                      <div className="p-2.5 rounded-lg border bg-rose-50 text-rose-800 border-rose-300 dark:bg-rose-950/60 dark:text-rose-300 dark:border-rose-800 text-[11px]">
                        Cảnh báo: Đối thủ đang bán dưới 80% giá vốn nhập kho.
                      </div>
                    )}
                  </div>
                </div>

                {/* Guardrail Notes Log */}
                {simulationResult.guardrail_notes.length > 0 && (
                  <div className="space-y-1.5 pt-2">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                      Ghi chú hệ thống
                    </span>
                    <div className="bg-slate-50 dark:bg-slate-800/40 p-3 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1">
                      {simulationResult.guardrail_notes.map((note, idx) => (
                        <p key={idx} className="text-xs text-slate-600 dark:text-slate-300 font-mono">
                          • {note}
                        </p>
                      ))}
                    </div>
                  </div>
                )}

                {/* Business Rationale */}
                <div className="space-y-1.5 pt-2 border-t border-slate-100 dark:border-slate-800">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                    Giải Trình Nghiệp Vụ
                  </span>
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-800/40 p-3 rounded-lg border border-slate-100 dark:border-slate-800">
                    {simulationResult.rationale}
                  </p>
                </div>
              </div>
            </>
          ) : (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-8 text-center text-xs text-slate-400 shadow-sm">
              Đang chờ dữ liệu mô phỏng...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
