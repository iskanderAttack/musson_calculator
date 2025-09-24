import streamlit as st
import math
import matplotlib.pyplot as plt
import pandas as pd

# Настройка страницы
st.set_page_config(
    page_title="Калькулятор печи Муссон",
    page_icon="🔥",
    layout="wide"
)

# --- Параметры материалов (теплопроводность, Вт/м·К) ---
MATERIALS = {
    "кирпич": 0.81,
    "газоблок": 0.12,
    "дерево": 0.18,
    "сэндвич-панель": 0.04,
    "керамзит блок": 0.43
}

# --- Модели "Муссон" ---
MUSSON_MODELS = {
    "Муссон 300": {"volume_l": 77, "price": 45000},
    "Муссон 600": {"volume_l": 125, "price": 65000},
    "Муссон 1000": {"volume_l": 200, "price": 85000},
    "Муссон 1500": {"volume_l": 311, "price": 110000},
    "Муссон 2000": {"volume_l": 467, "price": 135000},
}

# --- Плотность и теплотворная способность древесины ---
WOOD_TYPES = {
    "хвойные": {"density": 350, "q": 17},
    "берёза": {"density": 450, "q": 18},
    "дуб": {"density": 550, "q": 19.5},
    "липа": {"density": 500, "q": 17.5},
    "отходы": {"density": 700, "q": 12}  # средний для ЛДСП, ДСП, фанеры
}

# --- Функции расчёта ---

def calc_heat_loss(area_m2, height_m, wall_thickness_m, material, t_in, t_out, windows_m2=0, doors_m2=0, roof_insulation=True):
    volume_m3 = area_m2 * height_m
    lambda_wall = MATERIALS[material]
    r_wall = wall_thickness_m / lambda_wall
    wall_area = 2 * height_m * (math.sqrt(area_m2) * 4) - windows_m2 - doors_m2
    q_walls = wall_area * (t_in - t_out) / r_wall
    q_windows = windows_m2 * (t_in - t_out) / 0.4
    q_doors = doors_m2 * (t_in - t_out) / 0.6
    roof_r = 0.2 if not roof_insulation else 1.0
    q_roof = area_m2 * (t_in - t_out) / roof_r
    q_vent = 0.3 * volume_m3 * (t_in - t_out)
    total_w = q_walls + q_windows + q_doors + q_roof + q_vent
    return total_w / 1000


def musson_power(volume_l, fill_fraction, wood_type, efficiency, burn_hours):
    vol_m3 = volume_l / 1000
    filled_vol_m3 = vol_m3 * fill_fraction
    m_wood = filled_vol_m3 * WOOD_TYPES[wood_type]["density"]
    q_fuel = m_wood * WOOD_TYPES[wood_type]["q"]
    q_kwh = q_fuel / 3.6
    useful_kwh = q_kwh * efficiency
    p_kw = useful_kwh / burn_hours
    return useful_kwh, p_kw, m_wood


def calculate_fuel_consumption(daily_heat_loss_kwh, wood_energy_kwh_per_kg):
    return daily_heat_loss_kwh / wood_energy_kwh_per_kg

# --- Streamlit UI ---
st.title("🔥 Калькулятор подбора пиролизной печи Муссон")

st.sidebar.header("📐 Параметры здания")
col1, col2 = st.sidebar.columns(2)
with col1:
    area_m2 = st.number_input("Площадь помещения (м²)", 20, 500, 100)
with col2:
    height_m = st.number_input("Высота потолков (м)", 2.0, 5.0, 2.5)

material = st.sidebar.selectbox("Материал стен", list(MATERIALS.keys()))
wall_thickness = st.sidebar.slider("Толщина стен (см)", 10, 100, 40) / 100

st.sidebar.header("🪟 Дополнительные параметры")
windows_m2 = st.sidebar.number_input("Площадь окон (м²)", 0, 50, 5)
doors_m2 = st.sidebar.number_input("Площадь дверей (м²)", 0, 10, 2)
roof_insulation = st.sidebar.checkbox("Утеплённая крыша", value=True)

st.sidebar.header("🌡️ Климатические условия")
col1, col2 = st.sidebar.columns(2)
with col1:
    t_in = st.slider("Внутренняя температура (°C)", 15, 30, 22)
with col2:
    t_out = st.slider("Наружная температура (°C)", -50, 10, -20)

st.sidebar.header("🪵 Параметры топлива")
wood_type = st.sidebar.selectbox("Порода древесины", list(WOOD_TYPES.keys()))
wood_price_m3 = st.sidebar.number_input("Стоимость древесины (руб/м³)", 1000, 50000, 3500)
fill_fraction = st.sidebar.slider("Заполнение топки (%)", 50, 100, 85) / 100
efficiency = st.sidebar.slider("КПД пиролизного котла (%)", 70, 95, 88) / 100
burn_hours = st.sidebar.selectbox("Время горения одной закладки (ч)", [2, 4, 6, 8, 10], index=2)
working_day_hours = st.sidebar.selectbox("Режим работы печи (ч/день)", [6, 8, 10, 12, 14, 16], index=2)

# --- Расчёт ---
heat_loss_kw = calc_heat_loss(area_m2, height_m, wall_thickness, material, t_in, t_out, windows_m2, doors_m2, roof_insulation)
volume_m3 = area_m2 * height_m

st.header("Результаты расчёта")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Теплопотери здания", f"{heat_loss_kw:.1f} кВт")
with col2:
    st.metric("Рекомендуемая мощность", f"{heat_loss_kw * 1.2:.1f} кВт")
with col3:
    st.metric("Объём помещения", f"{volume_m3:.0f} м³")

st.subheader("🔥 Сравнение моделей Муссон")
results = []
for model, params in MUSSON_MODELS.items():
    useful_kwh, p_kw, m_wood = musson_power(params["volume_l"], fill_fraction, wood_type, efficiency, burn_hours)
    results.append({
        "model": model,
        "power": p_kw,
        "energy": useful_kwh,
        "wood_per_load": m_wood,
        "volume_l": params["volume_l"],
        "price": params["price"]
    })

df = pd.DataFrame(results)
df["Соответствие"] = df["power"] >= heat_loss_kw * 1.2
df["Рекомендация"] = df["Соответствие"].map({True: "✅ Подходит", False: "❌ Маломощна"})
display_df = df[["model", "power", "energy", "wood_per_load", "Рекомендация"]].copy()
display_df.columns = ["Модель", "Мощность (кВт)", "Энергия (кВт·ч)", "Дров за закладку (кг)", "Рекомендация"]
display_df["Мощность (кВт)"] = display_df["Мощность (кВт)"].round(1)
display_df["Энергия (кВт·ч)"] = display_df["Энергия (кВт·ч)"].round(0)
display_df["Дров за закладку (кг)"] = display_df["Дров за закладку (кг)"].round(1)
st.dataframe(display_df, use_container_width=True)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
models = [r["model"] for r in results]
powers = [r["power"] for r in results]
colors = ['green' if p >= heat_loss_kw * 1.2 else 'red' for p in powers]
ax1.bar(models, powers, color=colors, alpha=0.7)
ax1.axhline(y=heat_loss_kw * 1.2, color="blue", linestyle="--", label=f"Требуется: {heat_loss_kw * 1.2:.1f} кВт")
ax1.set_ylabel("Мощность, кВт")
ax1.set_title("Сравнение мощности моделей")
ax1.legend()
ax1.tick_params(axis='x', rotation=45)
energies = [r["energy"] for r in results]
ax2.bar(models, energies, color='orange', alpha=0.7)
ax2.set_ylabel("Энергия за закладку, кВт·ч")
ax2.set_title("Энергия от одной закладки дров")
ax2.tick_params(axis='x', rotation=45)
plt.tight_layout()
st.pyplot(fig)

st.subheader("💡 Рекомендации")
suitable_models = [r for r in results if r["power"] >= heat_loss_kw * 1.2]
if suitable_models:
    best_model = min(suitable_models, key=lambda x: x["price"])
    st.success(f"**Рекомендуемая модель: {best_model['model']}**")
    daily_heat_kwh = heat_loss_kw * working_day_hours
    wood_energy_kwh_kg = (WOOD_TYPES[wood_type]["q"] / 3.6) * efficiency
    daily_wood_kg = calculate_fuel_consumption(daily_heat_kwh, wood_energy_kwh_kg)
    st.write(f"• Примерный расход дров за день ({working_day_hours} ч): {daily_wood_kg:.1f} кг")
else:
    st.error("❌ Ни одна модель не покрывает теплопотери при текущих настройках")