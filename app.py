import streamlit as st
import pandas as pd
import csv
import random

st.set_page_config(
    page_title="TV Scheduling GA",
    page_icon="📺",
    layout="wide"
)

# Read CSV
def read_csv_to_dict(file_path):
    ratings = {}
    with open(file_path, encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)
        header = next(reader)
        slots = [int(x.replace("Hour ", "")) for x in header[1:]]
        for row in reader:
            if row and row[0].strip():
                ratings[row[0].strip()] = [float(x) for x in row[1:]]
    if not ratings or any(len(v) != len(slots) for v in ratings.values()):
        raise ValueError("Invalid ratings CSV.")
    return ratings, slots

def fitness(schedule, ratings):
    return sum(ratings[p][i] for i, p in enumerate(schedule))

def run_ga(ratings, slots, co_r, mut_r):
    random.seed(42)
    programs = list(ratings)
    population = [
        random.choices(programs, k=len(slots))
        for _ in range(50)
    ]
    history = []

    for generation in range(100):
        population.sort(
            key=lambda s: fitness(s, ratings),
            reverse=True
        )
        history.append(fitness(population[0], ratings))
        new_population = [s.copy() for s in population[:2]]

        while len(new_population) < 50:
            def select():
                candidates = random.sample(population, 3)
                return max(candidates, key=lambda s: fitness(s, ratings))

            p1, p2 = select(), select()

            if random.random() < co_r:
                point = random.randint(1, len(slots) - 1)
                c1 = p1[:point] + p2[point:]
                c2 = p2[:point] + p1[point:]
            else:
                c1, c2 = p1.copy(), p2.copy()

            if random.random() < mut_r:
                c1[random.randrange(len(slots))] = random.choice(programs)
            if random.random() < mut_r:
                c2[random.randrange(len(slots))] = random.choice(programs)

            new_population.extend(
                [c1, c2][:50 - len(new_population)]
            )

        population = new_population

    best = max(population, key=lambda s: fitness(s, ratings))
    history.append(fitness(best, ratings))
    return best, history

# Streamlit Interface
st.title("📺 TV Scheduling Using Genetic Algorithm")
st.write("Evolutionary Computing - JIE42903")

st.sidebar.header("GA Parameters")

co_r = st.sidebar.slider(
    "Crossover Rate (CO_R)",
    min_value=0.0,
    max_value=0.95,
    value=0.80,
    step=0.01
)

mut_r = st.sidebar.slider(
    "Mutation Rate (MUT_R)",
    min_value=0.01,
    max_value=0.20,
    value=0.20,
    step=0.01
)

st.sidebar.write("Generations: 100")
st.sidebar.write("Population Size: 50")
st.sidebar.write("Elitism Size: 2")

if st.button("Run Genetic Algorithm", type="primary"):
    try:
        ratings, slots = read_csv_to_dict(
            "/content/program_ratings_modified.csv"
        )
        best, history = run_ga(ratings, slots, co_r, mut_r)

        df = pd.DataFrame([
            {
                "Time": f"{hour:02d}:00",
                "Program": program,
                "Rating": ratings[program][i]
            }
            for i, (hour, program) in enumerate(zip(slots, best))
        ])

        st.success("Genetic Algorithm completed!")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Ratings", f"{fitness(best, ratings):.2f}")
        col2.metric("Initial Fitness", f"{history[0]:.2f}")
        col3.metric("Final Fitness", f"{history[-1]:.2f}")

        st.subheader("Final GA Schedule")
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader("Fitness Progress")
        st.line_chart(pd.DataFrame({"Best Fitness": history}))

        st.download_button(
            "Download Schedule CSV",
            df.to_csv(index=False),
            "ga_schedule.csv",
            "text/csv"
        )
    except Exception as e:
        st.error(f"Error: {e}")
