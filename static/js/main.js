const DEPT_MAP = {
  "01": "CSE", "02": "ECE", "03": "EEE", "04": "MECH",
  "05": "IT", "06": "EIE", "07": "BME", "08": "AERO",
  "09": "CIVIL", "10": "R&A", "11": "AI&DS", "53": "M.Tech CSE"
};

const YEAR_LABEL = {
  1: "I Year",
  2: "II Year",
  3: "III Year",
  4: "IV Year"
};

function parseRollNo(rollNo) {
  rollNo = rollNo.trim();
  if (rollNo.length < 11) return null;

  const yearCode = rollNo.substring(4, 6);
  const deptCode = rollNo.substring(6, 8);

  const currentYear = new Date().getFullYear();
  const joinYear = 2000 + parseInt(yearCode);
  const yearDiff = currentYear - joinYear;

  return {
    dept: DEPT_MAP[deptCode] || null,
    year: YEAR_LABEL[yearDiff] || null
  };
}

document.addEventListener("DOMContentLoaded", function () {
  const rollInput = document.getElementById("roll_no");
  if (!rollInput) return;

  rollInput.addEventListener("input", function () {
    const val = this.value.trim();
    if (val.length >= 11) {
      const parsed = parseRollNo(val);
      if (parsed) {
        const deptSelect = document.getElementById("department");
        if (deptSelect && parsed.dept) {
          for (let option of deptSelect.options) {
            if (option.value === parsed.dept) {
              option.selected = true;
              break;
            }
          }
        }
        const classInput = document.getElementById("class_name");
        if (classInput && parsed.year) {
          classInput.value = parsed.year;
        }
      }
    } else {
      const deptSelect = document.getElementById("department");
      if (deptSelect) deptSelect.selectedIndex = 0;
      const classInput = document.getElementById("class_name");
      if (classInput) classInput.value = "";
    }
  });
});

function toggleInput(type) {
  document.getElementById("input_type").value = type;
  document.getElementById("text-section").style.display = type === "text" ? "block" : "none";
  document.getElementById("image-section").style.display = type === "image" ? "block" : "none";
  document.getElementById("btn-text").className = "btn " + (type === "text" ? "btn-primary active" : "btn-outline-primary");
  document.getElementById("btn-image").className = "btn " + (type === "image" ? "btn-primary active" : "btn-outline-primary");
}
