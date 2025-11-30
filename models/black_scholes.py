import numpy as np
from scipy.stats import norm

N = norm.cdf
n = norm.pdf

def d1_d2(S, K, T, r, sigma):
    """
    Calculate d1 and d2 parameters for Black-Scholes.
    S: Spot price
    K: Strike price
    T: Time to expiration (in years)
    r: Risk-free interest rate
    sigma: Implied volatility
    """
    # Avoid division by zero and log of zero
    S = np.maximum(S, 1e-6)
    sigma = np.maximum(sigma, 1e-6)
    T = np.maximum(T, 1e-6)
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return d1, d2

def bs_price(S, K, T, r, sigma, option_type='call'):
    """
    Calculate Black-Scholes option price.
    option_type: 'call' or 'put'
    """
    d1, d2 = d1_d2(S, K, T, r, sigma)
    
    if option_type == 'call':
        price = S * N(d1) - K * np.exp(-r * T) * N(d2)
    else:
        price = K * np.exp(-r * T) * N(-d2) - S * N(-d1)
        
    return price

def calculate_greeks(S, K, T, r, sigma, option_type='call'):
    """
    Calculate all greeks.
    Returns dictionary with delta, gamma, theta, vega, rho.
    """
    d1, d2 = d1_d2(S, K, T, r, sigma)
    
    # Gamma (same for call and put)
    gamma = n(d1) / (S * sigma * np.sqrt(T))
    
    # Vega (same for call and put, usually divided by 100)
    vega = S * np.sqrt(T) * n(d1) / 100.0
    
    if option_type == 'call':
        delta = N(d1)
        theta = (- (S * n(d1) * sigma) / (2 * np.sqrt(T)) 
                 - r * K * np.exp(-r * T) * N(d2)) / 365.0
        rho = K * T * np.exp(-r * T) * N(d2) / 100.0
    else:
        delta = N(d1) - 1
        theta = (- (S * n(d1) * sigma) / (2 * np.sqrt(T)) 
                 + r * K * np.exp(-r * T) * N(-d2)) / 365.0
        rho = -K * T * np.exp(-r * T) * N(-d2) / 100.0
        
    return {
        'delta': delta,
        'gamma': gamma,
        'theta': theta,
        'vega': vega,
        'rho': rho
    }

def implied_volatility(price, S, K, T, r, option_type='call', tol=1e-5, max_iter=100):
    """
    Calculate Implied Volatility using Newton-Raphson method.
    """
    sigma = 0.5  # Initial guess
    
    for i in range(max_iter):
        P = bs_price(S, K, T, r, sigma, option_type)
        diff = price - P
        
        if abs(diff) < tol:
            return sigma
            
        d1, _ = d1_d2(S, K, T, r, sigma)
        vega = S * np.sqrt(T) * n(d1)
        
        if vega == 0:
            break
            
        sigma = sigma + diff / vega
        
        # Clamp sigma to reasonable bounds
        sigma = max(1e-4, min(sigma, 5.0))
        
    return sigma
