function toggleInput(type) {
  document.getElementById("input_type").value = type;
  document.getElementById("text-section").style.display = type === "text" ? "block" : "none";
  document.getElementById("image-section").style.display = type === "image" ? "block" : "none";
  document.getElementById("btn-text").className = "btn " + (type === "text" ? "btn-primary active" : "btn-outline-primary");
  document.getElementById("btn-image").className = "btn " + (type === "image" ? "btn-primary active" : "btn-outline-primary");
}
