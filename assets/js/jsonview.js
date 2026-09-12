function a(e) {
  return Array.isArray(e) ? "array" : e === null ? "null" : typeof e;
}
function f(e) {
  return document.createElement(e);
}
function I(e, t, n) {
  return e.addEventListener(t, n), () => e.removeEventListener(t, n);
}
function T(e) {
  e.parentNode.removeChild(e);
}
const i = {
  HIDDEN: "hidden",
  CARET_ICON: "caret-icon",
  CARET_RIGHT: "fa-caret-right",
  CARET_DOWN: "fa-caret-down",
  ICON: "fas",
  CONTAINER: "json-container"
};
function m(e = {}) {
  const { key: t, size: n, isExpanded: s = !1 } = e;
  return `
    <div class="line">
      <div class="caret-icon"><i class="fas ${s ? i.CARET_DOWN : i.CARET_RIGHT}"></i></div>
      <div class="json-key">${t}</div>
      <div class="json-size">${n}</div>
    </div>
  `;
}
function x(e = {}) {
  const { key: t, value: n, type: s } = e;
  return `
    <div class="line">
      <div class="empty-icon"></div>
      <div class="json-key">${t}</div>
      <div class="json-separator">:</div>
      <div class="json-value ${s}">${n}</div>
    </div>
  `;
}
function j() {
  const e = f("div");
  return e.className = i.CONTAINER, e;
}
function p(e) {
  e.children.forEach((t) => {
    t.el && t.el.classList.add(i.HIDDEN), t.isExpanded && p(t);
  });
}
function d(e) {
  e.children.forEach((t) => {
    t.el && t.el.classList.remove(i.HIDDEN), t.isExpanded && d(t);
  });
}
function y(e) {
  if (e.children.length > 0 && e.el) {
    const t = e.el.querySelector("." + i.ICON);
    t && t.classList.replace(i.CARET_RIGHT, i.CARET_DOWN);
  }
}
function E(e) {
  if (e.children.length > 0 && e.el) {
    const t = e.el.querySelector("." + i.ICON);
    t && t.classList.replace(i.CARET_DOWN, i.CARET_RIGHT);
  }
}
function v(e) {
  e.isExpanded ? (e.isExpanded = !1, E(e), p(e)) : (e.isExpanded = !0, y(e), d(e));
}
function O(e) {
  let t = f("div");
  const n = (r) => {
    const o = r.children.length;
    return r.type === "array" ? `[${o}]` : r.type === "object" ? `{${o}}` : null;
  }, s = (r) => {
    switch (r.type) {
      case "string":
        return r.value ? `${r.value}` : '""';
      case "number":
      case "boolean":
      case "null":
        return `${r.value}`;
      case "array":
        return `[${r.children.length}]`;
      case "object":
        return `{${r.children.length}}`;
      default:
        return `${r.value}`;
    }
  }, u = (r) => {
    switch (r.type) {
      case "string":
      case "number":
      case "boolean":
      case "null":
      case "array":
      case "object":
        return `json-${r.type}`;
      default:
        return `json-${typeof r.value}`;
    }
  };
  if (e.children.length > 0) {
    t.innerHTML = m({
      key: e.key,
      size: n(e),
      isExpanded: e.isExpanded
    });
    const r = t.querySelector("." + i.CARET_ICON);
    e.dispose = I(r, "click", () => v(e));
  } else
    t.innerHTML = x({
      key: e.key,
      value: s(e),
      type: u(e)
    });
  const c = t.children[0];
  return e.parent !== null && (e.isExpanded ? c.classList.remove(i.HIDDEN) : c.classList.add(i.HIDDEN)), c.style = "margin-left: " + e.depth * 18 + "px;", c;
}
function l(e, t) {
  t(e), e.children.length > 0 && e.children.forEach((n) => {
    l(n, t);
  });
}
function h(e = {}) {
  const t = (s) => a(s) === "object" && Object.keys(s).length === 0;
  let n = e.hasOwnProperty("value") ? e.value : null;
  return t(n) && (n = "{}"), {
    key: e.key || null,
    parent: e.parent || null,
    value: n,
    isExpanded: e.isExpanded || !1,
    type: e.type || null,
    children: e.children || [],
    el: e.el || null,
    depth: e.depth || 0,
    dispose: null
  };
}
function N(e, t) {
  if (typeof e == "object")
    for (let n in e) {
      const s = h({
        value: e[n],
        key: n,
        depth: t.depth + 1,
        type: a(e[n]),
        parent: t
      });
      t.children.push(s), N(e[n], s);
    }
}
function C(e) {
  return typeof e == "string" ? JSON.parse(e) : e;
}
function g(e) {
  const t = C(e), n = h({
    value: t,
    key: a(t),
    type: a(t)
  });
  return N(t, n), n;
}
function R(e, t) {
  const n = C(e), s = g(n);
  return D(s, t), s;
}
function D(e, t) {
  const n = j();
  l(e, function(s) {
    s.el = O(s), n.appendChild(s.el);
  }), t.appendChild(n);
}
function $(e) {
  l(e, function(t) {
    t.el && t.el.classList.remove(i.HIDDEN), t.isExpanded = !0, y(t);
  });
}
function k(e) {
  l(e, function(t) {
    t.isExpanded = !1, t.depth > e.depth && t.el && t.el.classList.add(i.HIDDEN), E(t);
  });
}
function A(e) {
  l(e, (t) => {
    t.dispose && t.dispose();
  }), T(e.el.parentNode);
}
const H = {
  toggleNode: v,
  render: D,
  create: g,
  renderJSON: R,
  expand: $,
  collapse: k,
  traverse: l,
  destroy: A
};
export {
  k as collapse,
  g as create,
  H as default,
  A as destroy,
  $ as expand,
  D as render,
  R as renderJSON,
  v as toggleNode,
  l as traverse
};
