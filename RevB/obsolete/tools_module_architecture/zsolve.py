import sys
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

EPS0 = 8.854187817e-12
C0 = 299792458.0

def capacitance(w, h, t, er, d, gap=None, mask=0.0, er_mask=3.8, width=None, height=2.0):
    width = width or max(6.0, 10 * w)
    nx = int(round(width / d)) + 1
    ny = int(round(height / d)) + 1
    jg = 0
    jt0 = int(round(h / d))
    jt1 = jt0 + max(1, int(round(t / d)))
    xc = width / 2
    i0 = int(round((xc - w / 2) / d))
    i1 = int(round((xc + w / 2) / d))
    epsc = np.ones((nx - 1, ny - 1))
    epsc[:, :jt0] = er
    if mask > 0:
        jm = jt0 + int(round(mask / d))
        epsc[:, jt0:jm] = er_mask
    fixed = np.zeros((nx, ny), dtype=bool)
    val = np.zeros((nx, ny))
    fixed[:, jg] = True
    fixed[0, :] = True
    fixed[-1, :] = True
    fixed[:, -1] = True
    fixed[i0:i1 + 1, jt0:jt1 + 1] = True
    val[i0:i1 + 1, jt0:jt1 + 1] = 1.0
    if gap is not None:
        g0 = int(round((xc - w / 2 - gap) / d))
        g1 = int(round((xc + w / 2 + gap) / d))
        fixed[:g0 + 1, jt0:jt1 + 1] = True
        fixed[g1:, jt0:jt1 + 1] = True
    idx = -np.ones((nx, ny), dtype=np.int64)
    free = ~fixed
    idx[free] = np.arange(free.sum())
    n = int(free.sum())
    rows, cols, data = [], [], []
    b = np.zeros(n)
    def ecell(i, j):
        if 0 <= i < nx - 1 and 0 <= j < ny - 1:
            return epsc[i, j]
        return None
    ex = np.zeros((nx - 1, ny))
    for j in range(ny):
        a = epsc[:, j] if j < ny - 1 else epsc[:, j - 1]
        c = epsc[:, j - 1] if j > 0 else epsc[:, j]
        ex[:, j] = 0.5 * (a + c)
    ey = np.zeros((nx, ny - 1))
    for i in range(nx):
        a = epsc[i, :] if i < nx - 1 else epsc[i - 1, :]
        c = epsc[i - 1, :] if i > 0 else epsc[i, :]
        ey[i, :] = 0.5 * (a + c)
    I, J = np.nonzero(free)
    k = idx[I, J]
    diag = np.zeros(n)
    for di, dj, coef in ((1, 0, ex[I, J] if True else None), (-1, 0, None), (0, 1, None), (0, -1, None)):
        pass
    nb = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    for di, dj in nb:
        In, Jn = I + di, J + dj
        if di == 1:
            c = ex[I, J]
        elif di == -1:
            c = ex[I - 1, J]
        elif dj == 1:
            c = ey[I, J]
        else:
            c = ey[I, J - 1]
        diag += c
        isfree = free[In, Jn]
        rows.append(k[isfree]); cols.append(idx[In[isfree], Jn[isfree]]); data.append(-c[isfree])
        np.add.at(b, k[~isfree], c[~isfree] * val[In[~isfree], Jn[~isfree]])
    rows.append(k); cols.append(k); data.append(diag)
    A = sp.csr_matrix((np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))), shape=(n, n))
    x = spla.spsolve(A, b)
    V = val.copy()
    V[free] = x
    W = (ex * (V[1:, :] - V[:-1, :]) ** 2).sum() + (ey * (V[:, 1:] - V[:, :-1]) ** 2).sum()
    return W * EPS0

def z0(w, h, t, er, d, gap=None, mask=0.0):
    C = capacitance(w, h, t, er, d, gap, mask)
    Ca = capacitance(w, h, t, 1.0, d, gap, 0.0 if mask == 0 else mask, er_mask=1.0)
    z = 1.0 / (C0 * np.sqrt(C * Ca))
    eeff = C / Ca
    return z, eeff

def hammerstad(w, h, er):
    u = w / h
    eeff = (er + 1) / 2 + (er - 1) / 2 * (1 + 12 / u) ** -0.5
    if u <= 1:
        return 60 / np.sqrt(eeff) * np.log(8 / u + u / 4), eeff
    return 120 * np.pi / (np.sqrt(eeff) * (u + 1.393 + 0.667 * np.log(u + 1.444))), eeff

if __name__ == "__main__":
    H, T, ER = 0.2104, 0.035, 4.4
    print("JLC04161H-7628 L1 over L2: h = 0.2104 mm prepreg (7628, er 4.4 per stackup file), t = 0.035 mm, no solder mask unless stated")
    for d in (0.01, 0.005):
        z, e = z0(0.36, H, T, ER, d)
        print(f"grid {d} mm: microstrip w=0.36 -> Z0 {z:.1f} ohm, eeff {e:.2f}")
    print("width sweep (grid 0.005 mm):")
    for w in (0.30, 0.33, 0.36, 0.38, 0.40):
        z, e = z0(w, H, T, ER, 0.005)
        zh, eh = hammerstad(w, H, ER)
        print(f"  microstrip w={w:.2f}: FD {z:.1f} ohm (eeff {e:.2f}) | Hammerstad {zh:.1f} ohm")
    for w, g in ((0.30, 0.15), (0.34, 0.20), (0.36, 0.25)):
        z, e = z0(w, H, T, ER, 0.005, gap=g)
        print(f"  CPWG w={w:.2f} gap={g:.2f}: FD {z:.1f} ohm (eeff {e:.2f})")
    z, e = z0(0.36, H, T, ER, 0.005, mask=0.02)
    print(f"  microstrip w=0.36 with 20 um solder mask (er 3.8, assumed): FD {z:.1f} ohm")
