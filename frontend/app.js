const API_BASE = "";
const authStatus = document.getElementById("authStatus");
const loginBtn = document.getElementById("loginBtn");
const registerBtn = document.getElementById("registerBtn");
const createProjectBtn = document.getElementById("createProject");
const projectList = document.getElementById("projectList");
const refreshProjects = document.getElementById("refreshProjects");

const tabs = document.querySelectorAll(".tab");
const tabContents = document.querySelectorAll(".tab-content");

const setStatus = (msg, isError = false) => {
  authStatus.textContent = msg;
  authStatus.style.color = isError ? "#ff6b6b" : "#6ee7b7";
};

const tokenKey = "engspec_token";

const setToken = (token) => {
  localStorage.setItem(tokenKey, token);
};

const getToken = () => localStorage.getItem(tokenKey);

const apiFetch = async (path, options = {}) => {
  const headers = options.headers || {};
  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Erro na requisição");
  }
  return data;
};

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((t) => t.classList.remove("active"));
    tabContents.forEach((content) => content.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(tab.dataset.tab).classList.add("active");
    setStatus("");
  });
});

loginBtn?.addEventListener("click", async () => {
  const email = document.getElementById("loginEmail").value;
  const password = document.getElementById("loginPassword").value;
  try {
    const data = await apiFetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    setToken(data.token);
    setStatus("Login efetuado! Carregando projetos...");
    await loadProjects();
  } catch (err) {
    setStatus(err.message, true);
  }
});

registerBtn?.addEventListener("click", async () => {
  const email = document.getElementById("registerEmail").value;
  try {
    const data = await apiFetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    if (data.token) {
      setStatus(`Token gerado: ${data.token}`);
      return;
    }
    setStatus("Confirmação enviada. Verifique seu e-mail.");
  } catch (err) {
    setStatus(err.message, true);
  }
});

const loadProjects = async () => {
  if (!getToken()) {
    projectList.innerHTML = "<p class=\"muted\">Faça login para ver seus projetos.</p>";
    return;
  }
  try {
    const projects = await apiFetch("/api/projects");
    if (!projects.length) {
      projectList.innerHTML = "<p class=\"muted\">Nenhum projeto criado ainda.</p>";
      return;
    }
    projectList.innerHTML = projects
      .map(
        (project) => `
        <div class="project-card">
          <strong>${project.name}</strong>
          <div class="muted">${project.service_type} • ${project.status}</div>
        </div>
      `
      )
      .join("");
  } catch (err) {
    projectList.innerHTML = `<p class=\"muted\">${err.message}</p>`;
  }
};

createProjectBtn?.addEventListener("click", async () => {
  const name = document.getElementById("projectName").value;
  const serviceType = document.getElementById("serviceType").value;
  try {
    await apiFetch("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, service_type: serviceType }),
    });
    setStatus("Projeto criado!");
    await loadProjects();
  } catch (err) {
    setStatus(err.message, true);
  }
});

refreshProjects?.addEventListener("click", loadProjects);

document.getElementById("demoScroll")?.addEventListener("click", () => {
  document.getElementById("dashboard")?.scrollIntoView({ behavior: "smooth" });
});

loadProjects();
