import sys

with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the giant Promise.all with decoupled fetches
old_fetch = '''      const [resCurrent, resSeq, resWards, resRisk] = await Promise.all([
        fetch(/api/v1/thermal/current?lat=${LAT}&lon=${LON}),
        fetch(/api/v1/forecast/sequence?latitude=${LAT}&longitude=${LON}),
        fetch(/api/v1/wards/weather),
        fetch(/api/v1/risk/forecast?lat=${LAT}&lon=${LON})
      ]);
      
      const curr = await resCurrent.json();
      const seq = await resSeq.json();
      const wrd = await resWards.json();
      const risk = await resRisk.json();
      
      setCurrentData(curr);
      setSeqData(seq);
      setWardsData(wrd?.wards || []);
      setRiskData(risk);'''

new_fetch = '''      // Decouple wards fetch to prevent blocking the main dashboard
      const [resCurrent, resSeq, resRisk] = await Promise.all([
        fetch(/api/v1/thermal/current?lat=&lon=),
        fetch(/api/v1/forecast/sequence?latitude=&longitude=),
        fetch(/api/v1/risk/forecast?lat=&lon=)
      ]);
      
      setCurrentData(await resCurrent.json());
      setSeqData(await resSeq.json());
      setRiskData(await resRisk.json());
      
      // Fetch wards in background
      fetch(/api/v1/wards/weather)
        .then(res => res.json())
        .then(data => setWardsData(data?.wards || []))
        .catch(e => console.error("Wards fetch failed:", e));
'''

new_content = content.replace(old_fetch, new_fetch)
with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(new_content)
print("Updated frontend fetch logic.")
