from .initial_guess import *
from .solve_eq import *
from .solve import *
if USE_JAX:
    from jax import jacfwd
    from jax import ops

def calc_IV( dgrid , Vincrement , eps , Chi , Eg , Nc , Nv , Ndop , mn , mp , Et , tn , tp , Br , Cn , Cp , Snl , Spl , Snr , Spr , G_used ):
    """
    Compute the I-V curve.

    Parameters
    ----------
        dgrid      : numpy array , shape = ( N - 1 )
            array of distances between consecutive grid points
        Vincrement : float
            increment voltage for I-V curve
        eps        : numpy array , shape = ( N )
            relative dieclectric constant
        Chi        : numpy array , shape = ( N )
            electron affinity
        Eg         : numpy array , shape = ( N )
            band gap
        Nc         : numpy array , shape = ( N )
            e- density of states
        Nv         : numpy array , shape = ( N )
            hole density of states
        Ndop       : numpy array , shape = ( N )
            dopant density ( positive for donors , negative for acceptors )
        mn         : numpy array , shape = ( N )
            e- mobility
        mp         : numpy array , shape = ( N )
            hole mobility
        Et         : numpy array , shape = ( N )
            SHR trap state energy level
        tn         : numpy array , shape = ( N )
            SHR e- lifetime
        tp         : numpy array , shape = ( N )
            SHR hole lifetime
        Br         : numpy array , shape = ( N )
            radiative recombination coefficient
        Cn         : numpy array , shape = ( N )
            electron Auger coefficient
        Cp         : numpy array , shape = ( N )
            hole Auger coefficient
        Snl        : float
            e- surface recombination velocity at left boundary
        Spl        : float
            hole surface recombination velocity at left boundary
        Snr        : float
            e- surface recombination velocity at right boundary
        Spr        : float
            hole surface recombination velocity at right boundary
        G_used     : numpy array , shape = ( N )
            e-/hole pair generation rate density ( computed or user defined )

    Returns
    -------
        numpy array , shape = ( L <= max_iter )
            array of total currents, if length L < max_iter, current switched signs

    """
    scale = scales()
    N = dgrid.size + 1

    phi_ini = eq_init_phi( Chi , Eg , Nc , Nv , Ndop )
    phi_eq = solve_eq( dgrid , phi_ini , eps , Chi , Eg , Nc , Nv , Ndop )
    neq_0 = Nc[0] * np.exp( Chi[0] + phi_eq[0] )
    neq_L = Nc[-1] * np.exp( Chi[-1] + phi_eq[-1] )
    peq_0 = Nv[0] * np.exp( - Chi[0] - Eg[0] - phi_eq[0] )
    peq_L = Nv[-1] * np.exp( - Chi[-1] - Eg[-1] - phi_eq[-1] )

    phis = np.concatenate( ( np.zeros( 2*N ) , phi_eq ) , axis = 0 )
    max_iter = 100
    iter = 0
    current = []
    cond = True
    v = 0

    while cond and ( iter < max_iter ):
        print( 'V = {0:.7f}   Iteration       |F(x)|                Residual     '.format( scale['E'] * v ) )
        print( '-------------------------------------------------------------------' )
        sol = solve( dgrid , neq_0 , neq_L , peq_0 , peq_L , phis , eps , Chi , Eg , Nc , Nv , Ndop , mn , mp , Et , tn , tp , Br , Cn , Cp , Snl , Spl , Snr , Spr , G_used )
        tot_current , _ = total_current( dgrid , sol[0:N] , sol[N:2*N] , sol[2*N:] , Chi , Eg , Nc , Nv , mn , mp )
        current.append( tot_current )
        if ( len( current ) > 1 ):
            cond = ( current[-2] * current[-1] > 0 )
        iter += 1
        v = v + Vincrement
        if USE_JAX:
            phis = ops.index_update( sol , -1 , phi_eq[-1] + v )
        else:
            sol[-1] = phi_eq[-1] + v
            phis = sol

    return np.array( current , dtype = np.float64 )





def grad_IV( dgrid , Vincrement , eps , Chi , Eg , Nc , Nv , Ndop , mn , mp , Et , tn , tp , Br , Cn , Cp , Snl , Spl , Snr , Spr , G_used ):
    """
    Compute the I-V curve and the derivatives of the currents in the I-V curve with respect to the material properties.

    Parameters
    ----------
        dgrid      : numpy array , shape = ( N - 1 )
            array of distances between consecutive grid points
        Vincrement : float
            increment voltage for I-V curve
        eps        : numpy array , shape = ( N )
            relative dieclectric constant
        Chi        : numpy array , shape = ( N )
            electron affinity
        Eg         : numpy array , shape = ( N )
            band gap
        Nc         : numpy array , shape = ( N )
            e- density of states
        Nv         : numpy array , shape = ( N )
            hole density of states
        Ndop       : numpy array , shape = ( N )
            dopant density ( positive for donors , negative for acceptors )
        mn         : numpy array , shape = ( N )
            e- mobility
        mp         : numpy array , shape = ( N )
            hole mobility
        Et         : numpy array , shape = ( N )
            SHR trap state energy level
        tn         : numpy array , shape = ( N )
            SHR e- lifetime
        tp         : numpy array , shape = ( N )
            SHR hole lifetime
        Br         : numpy array , shape = ( N )
            radiative recombination coefficient
        Cn         : numpy array , shape = ( N )
            electron Auger coefficient
        Cp         : numpy array , shape = ( N )
            hole Auger coefficient
        Snl        : float
            e- surface recombination velocity at left boundary
        Spl        : float
            hole surface recombination velocity at left boundary
        Snr        : float
            e- surface recombination velocity at right boundary
        Spr        : float
            hole surface recombination velocity at right boundary
        G_used     : numpy array , shape = ( N )
            e-/hole pair generation rate density ( computed or user defined )


    Returns
    -------
        current     : numpy array , shape = ( L <= max_iter )
            array of total currents, if length L < max_iter, current switched signs
        current_jac : dictionnary of numpy arrays , shape = ( L x N ) ( 19 keys )
            derivatives of the total currents
            'eps'  -> derivative with respect to eps
            'Chi'  -> derivative with respect to Chi
            'Eg'   -> derivative with respect to Eg
            'Nc'   -> derivative with respect to Nc
            'Nv'   -> derivative with respect to Nv
            'Ndop' -> derivative with respect to Ndop
            'mn'   -> derivative with respect to mn
            'mp'   -> derivative with respect to mp
            'Et'   -> derivative with respect to Et
            'tn'   -> derivative with respect to tn
            'tp'   -> derivative with respect to tp
            'Br'   -> derivative with respect to B
            'Cn'   -> derivative with respect to Cn
            'Cp'   -> derivative with respect to Cp
            'Snl'  -> derivative with respect to Snl
            'Spl'  -> derivative with respect to Spl
            'Snr'  -> derivative with respect to Snr
            'Spr'  -> derivative with respect to Spr
            'G'    -> derivative with respect to G

    """
    grad_phieq = jit( jacfwd( solve_eq_forgrad , argnums = ( 1 , 2 , 3 , 4 , 5 , 6 , 7 ) ) )
    grad_solve = jit( jacfwd( solve_forgrad , argnums = ( 1 , 2 , 3 , 4 , 5 , 6 , 7 , 8 , 9 , 10 , 11 , 12 , 13 , 14 , 15 , 16 , 17 , 18 , 19 , 20 , 21 , 22 , 23 , 24 ) ) )

    N = dgrid.size + 1

    phi_ini = eq_init_phi( Chi , Eg , Nc , Nv , Ndop )
    dphi_ini_dChi0 , dphi_ini_dEg0 , dphi_ini_dNc0 , dphi_ini_dNv0 , dphi_ini_dNdop0 , dphi_ini_dChiL , dphi_ini_dEgL , dphi_ini_dNcL , dphi_ini_dNvL , dphi_ini_dNdopL = eq_init_phi_deriv( Chi , Eg , Nc , Nv , Ndop )

    phi_eq = solve_eq_forgrad( dgrid , phi_ini , eps , Chi , Eg , Nc , Nv , Ndop )
    neq_0 = Nc[0] * np.exp( Chi[0] + phi_eq[0] )
    neq_L = Nc[-1] * np.exp( Chi[-1] + phi_eq[-1] )
    peq_0 = Nv[0] * np.exp( - Chi[0] - Eg[0] - phi_eq[0] )
    peq_L = Nv[-1] * np.exp( - Chi[-1] - Eg[-1] - phi_eq[-1] )

    gradphieq = grad_phieq( dgrid , phi_ini , eps , Chi , Eg , Nc , Nv , Ndop )

    dphi_eq_deps = gradphieq[ 1 ]
    dphi_eq_dChi = gradphieq[ 2 ]
    dphi_eq_dChi = ops.index_add( dphi_eq_dChi , ops.index[:,0] , np.dot( gradphieq[ 0 ] , dphi_ini_dChi0 ) )
    dphi_eq_dChi = ops.index_add( dphi_eq_dChi , ops.index[:,-1] , np.dot( gradphieq[ 0 ] , dphi_ini_dChiL ) )
    dphi_eq_dEg = gradphieq[ 3 ]
    dphi_eq_dEg = ops.index_add( dphi_eq_dEg , ops.index[:,0] , np.dot( gradphieq[ 0 ] , dphi_ini_dEg0 ) )
    dphi_eq_dEg = ops.index_add( dphi_eq_dEg , ops.index[:,-1] , np.dot( gradphieq[ 0 ] , dphi_ini_dEgL ) )
    dphi_eq_dNc = gradphieq[ 4 ]
    dphi_eq_dNc = ops.index_add( dphi_eq_dNc , ops.index[:,0] , np.dot( gradphieq[ 0 ] , dphi_ini_dNc0 ) )
    dphi_eq_dNc = ops.index_add( dphi_eq_dNc , ops.index[:,-1] , np.dot( gradphieq[ 0 ] , dphi_ini_dNcL ) )
    dphi_eq_dNv = gradphieq[ 5 ]
    dphi_eq_dNv = ops.index_add( dphi_eq_dNv , ops.index[:,0] , np.dot( gradphieq[ 0 ] , dphi_ini_dNv0 ) )
    dphi_eq_dNv = ops.index_add( dphi_eq_dNv , ops.index[:,-1] , np.dot( gradphieq[ 0 ] , dphi_ini_dNvL ) )
    dphi_eq_dNdop = gradphieq[ 6 ]
    dphi_eq_dNdop = ops.index_add( dphi_eq_dNdop , ops.index[:,0] , np.dot( gradphieq[ 0 ] , dphi_ini_dNdop0 ) )
    dphi_eq_dNdop = ops.index_add( dphi_eq_dNdop , ops.index[:,-1] , np.dot( gradphieq[ 0 ] , dphi_ini_dNdopL ) )

    dneq0_dChi = np.concatenate( ( np.array( [ neq_0 ] ) , np.zeros( N - 1 ) ) , axis = 0 ) + neq_0 * dphi_eq_dChi[0,:]
    dneqL_dChi = np.concatenate( ( np.zeros( N - 1 ) , np.array( [ neq_L ] ) ) , axis = 0 ) + neq_L * dphi_eq_dChi[-1,:]
    dneq0_dEg = neq_0 * dphi_eq_dEg[0,:]
    dneqL_dEg = neq_L * dphi_eq_dEg[-1,:]
    dneq0_dNc = np.concatenate( ( np.array( [ np.exp( Chi[0] + phi_eq[0] ) ] ) , np.zeros( N - 1 ) ) , axis = 0 ) + neq_0 * dphi_eq_dNc[0,:]
    dneqL_dNc = np.concatenate( ( np.zeros( N - 1 ) , np.array( [ np.exp( Chi[-1] + phi_eq[-1] ) ] ) ) , axis = 0 ) + neq_L * dphi_eq_dNc[-1,:]
    dneq0_dNv = neq_0 * dphi_eq_dNv[0,:]
    dneqL_dNv = neq_L * dphi_eq_dNv[-1,:]
    dneq0_dNdop = neq_0 * dphi_eq_dNdop[0,:]
    dneqL_dNdop = neq_L * dphi_eq_dNdop[-1,:]

    dpeq0_dChi = np.concatenate( ( np.array( [ - peq_0 ] ) , np.zeros( N - 1 ) ) , axis = 0 ) - peq_0 * dphi_eq_dChi[0,:]
    dpeqL_dChi = np.concatenate( ( np.zeros( N - 1 ) , np.array( [ - peq_L ] ) ) , axis = 0 ) - peq_L * dphi_eq_dChi[-1,:]
    dpeq0_dEg = - peq_0 * dphi_eq_dEg[0,:]
    dpeqL_dEg = - peq_L * dphi_eq_dEg[-1,:]
    dpeq0_dNc = np.concatenate( ( np.array( [ np.exp( - Chi[0] - Eg[0] - phi_eq[0] ) ] ) , np.zeros( N - 1 ) ) , axis = 0 ) - peq_0 * dphi_eq_dNc[0,:]
    dpeqL_dNc = np.concatenate( ( np.zeros( N - 1 ) , np.array( [ np.exp( - Chi[-1] - Eg[-1] - phi_eq[-1] ) ] ) ) , axis = 0 ) - peq_L * dphi_eq_dNc[-1,:]
    dpeq0_dNv = - peq_0 * dphi_eq_dNv[0,:]
    dpeqL_dNv = - peq_L * dphi_eq_dNv[-1,:]
    dpeq0_dNdop = - peq_0 * dphi_eq_dNdop[0,:]
    dpeqL_dNdop = - peq_L * dphi_eq_dNdop[-1,:]

    phis = np.concatenate( ( np.zeros( 2*N ) , phi_eq ) , axis = 0 )
    jac_phis = {}
    jac_phis['eps'] = np.vstack( ( np.zeros( ( 2*N , N ) ) , dphi_eq_deps ) )
    jac_phis['Chi'] = np.vstack( ( np.zeros( ( 2*N , N ) ) , dphi_eq_dChi ) )
    jac_phis['Eg'] = np.vstack( ( np.zeros( ( 2*N , N ) ) , dphi_eq_dEg ) )
    jac_phis['Nc'] = np.vstack( ( np.zeros( ( 2*N , N ) ) , dphi_eq_dNc ) )
    jac_phis['Nv'] = np.vstack( ( np.zeros( ( 2*N , N ) ) , dphi_eq_dNv ) )
    jac_phis['Ndop'] = np.vstack( ( np.zeros( ( 2*N , N ) ) , dphi_eq_dNdop ) )
    jac_phis['Et'] = np.zeros( ( 3*N , N ) )
    jac_phis['tn'] = np.zeros( ( 3*N , N ) )
    jac_phis['tp'] = np.zeros( ( 3*N , N ) )
    jac_phis['Br'] = np.zeros( ( 3*N , N ) )
    jac_phis['Cn'] = np.zeros( ( 3*N , N ) )
    jac_phis['Cp'] = np.zeros( ( 3*N , N ) )
    jac_phis['mn'] = np.zeros( ( 3*N , N ) )
    jac_phis['mp'] = np.zeros( ( 3*N , N ) )
    jac_phis['Snl'] = np.zeros( ( 3*N , N ) )
    jac_phis['Spl'] = np.zeros( ( 3*N , N ) )
    jac_phis['Snr'] = np.zeros( ( 3*N , N ) )
    jac_phis['Spr'] = np.zeros( ( 3*N , N ) )
    jac_phis['G'] = np.zeros( ( 3*N , N ) )

    max_iter = 100
    iter = 0
    current = []
    current_jac = []
    cond = True
    v = 0

    while cond and ( iter < max_iter ):
        sol = solve_forgrad( dgrid , neq_0 , neq_L , peq_0 , peq_L , phis , eps , Chi , Eg , Nc , Nv , Ndop , mn , mp , Et , tn , tp , Br , Cn , Cp , Snl , Spl , Snr , Spr , G_used )
        gradsol = grad_solve( dgrid , neq_0 , neq_L , peq_0 , peq_L , phis , eps , Chi , Eg , Nc , Nv , Ndop , Et , tn , tp , Br , Cn , Cp , mn , mp , Snl , Spl , Snr , Spr , G_used )

        tot_current, tot_current_derivs = total_current( sol[0:N] , sol[N:2*N] , sol[2*N:] , dgrid , Chi , Eg , Nc , Nv , mn , mp )
        current.append( tot_current )

        current.append( tot_current )

        jac_phis['eps'] = gradsol[5] + np.dot( gradsol[4] , jac_phis['eps'] )
        jac_phis['Chi'] = gradsol[6] + np.dot( np.reshape( gradsol[0] , ( 3 * N , 1 ) ) , np.reshape( dneq0_dChi , ( 1 , N ) ) ) + np.dot( np.reshape( gradsol[1] , ( 3 * N , 1 ) ) , np.reshape( dneqL_dChi , ( 1 , N ) ) ) + np.dot( np.reshape( gradsol[2] , ( 3 * N , 1 ) ) , np.reshape( dpeq0_dChi , ( 1 , N ) ) ) + np.dot( np.reshape( gradsol[3] , ( 3 * N , 1 ) ) , np.reshape( dpeqL_dChi , ( 1 , N ) ) ) + np.dot( gradsol[4] , jac_phis['Chi'] )
        jac_phis['Eg'] = gradsol[7] + np.dot( np.reshape( gradsol[0] , ( 3 * N , 1 ) ) , np.reshape( dneq0_dEg , ( 1 , N ) ) ) + np.dot( np.reshape( gradsol[1] , ( 3 * N , 1 ) ) , np.reshape( dneqL_dEg , ( 1 , N ) ) ) + np.dot( np.reshape( gradsol[2] , ( 3 * N , 1 ) ) , np.reshape( dpeq0_dEg , ( 1 , N ) ) ) + np.dot( np.reshape( gradsol[3] , ( 3 * N , 1 ) ) , np.reshape( dpeqL_dEg , ( 1 , N ) ) )+ np.dot( gradsol[4] , jac_phis['Eg'] )
        jac_phis['Nc'] = gradsol[8] + np.dot( np.reshape( gradsol[0] , ( 3 * N , 1 ) ) , np.reshape( dneq0_dNc , ( 1 , N ) ) ) + np.dot( np.reshape( gradsol[1] , ( 3 * N , 1 ) ) , np.reshape( dneqL_dNc , ( 1 , N ) ) ) + np.dot( np.reshape( gradsol[2] , ( 3 * N , 1 ) ) , np.reshape( dpeq0_dNc , ( 1 , N ) ) ) + np.dot( np.reshape( gradsol[3] , ( 3 * N , 1 ) ) , np.reshape( dpeqL_dNc , ( 1 , N ) ) )+ np.dot( gradsol[4] , jac_phis['Nc'] )
        jac_phis['Nv'] = gradsol[9] + np.dot( np.reshape( gradsol[0] , ( 3 * N , 1 ) ) , np.reshape( dneq0_dNv , ( 1 , N ) ) ) + np.dot( np.reshape( gradsol[1] , ( 3 * N , 1 ) ) , np.reshape( dneqL_dNv , ( 1 , N ) ) ) + np.dot( np.reshape( gradsol[2] , ( 3 * N , 1 ) ) , np.reshape( dpeq0_dNv , ( 1 , N ) ) ) + np.dot( np.reshape( gradsol[3] , ( 3 * N , 1 ) ) , np.reshape( dpeqL_dNv , ( 1 , N ) ) )+ np.dot( gradsol[4] , jac_phis['Nv'] )
        jac_phis['Ndop'] = gradsol[10] + np.dot( np.reshape( gradsol[0] , ( 3 * N , 1 ) ) , np.reshape( dneq0_dNdop , ( 1 , N ) ) ) + np.dot( np.reshape( gradsol[1] , ( 3 * N , 1 ) ) , np.reshape( dneqL_dNdop , ( 1 , N ) ) ) + np.dot( np.reshape( gradsol[2] , ( 3 * N , 1 ) ) , np.reshape( dpeq0_dNdop , ( 1 , N ) ) ) + np.dot( np.reshape( gradsol[3] , ( 3 * N , 1 ) ) , np.reshape( dpeqL_dNdop , ( 1 , N ) ) )+ np.dot( gradsol[4] , jac_phis['Ndop'] )
        jac_phis['Et'] = gradsol[11] + np.dot( gradsol[4] , jac_phis['Et'] )
        jac_phis['tn'] = gradsol[12] + np.dot( gradsol[4] , jac_phis['tn'] )
        jac_phis['tp'] = gradsol[13] + np.dot( gradsol[4] , jac_phis['tp'] )
        jac_phis['Br'] = gradsol[14] + np.dot( gradsol[4] , jac_phis['Br'] )
        jac_phis['Cn'] = gradsol[15] + np.dot( gradsol[4] , jac_phis['Cn'] )
        jac_phis['Cp'] = gradsol[16] + np.dot( gradsol[4] , jac_phis['Cp'] )
        jac_phis['mn'] = gradsol[17] + np.dot( gradsol[4] , jac_phis['mn'] )
        jac_phis['mp'] = gradsol[18] + np.dot( gradsol[4] , jac_phis['mp'] )
        jac_phis['Snl'] = gradsol[19] + np.dot( gradsol[4] , jac_phis['Snl'] )
        jac_phis['Spl'] = gradsol[20] + np.dot( gradsol[4] , jac_phis['Spl'] )
        jac_phis['Snr'] = gradsol[21] + np.dot( gradsol[4] , jac_phis['Snr'] )
        jac_phis['Spr'] = gradsol[22] + np.dot( gradsol[4] , jac_phis['Spr'] )
        jac_phis['G'] = gradsol[23] + np.dot( gradsol[4] , jac_phis['G'] )

        new_current_jac = {}

        new_current_jac['eps'] = \
        tot_current_derivs['dphin0'] * jac_phis['eps'][0,:] \
        + tot_current_derivs['dphin1'] * jac_phis['eps'][1,:] \
        + tot_current_derivs['dphin0'] * jac_phis['eps'][N,:] \
        + tot_current_derivs['dphin1'] * jac_phis['eps'][N+1,:]
        + tot_current_derivs['dphi0'] * jac_phis['eps'][2*N,:] \
        + tot_current_derivs['dphi1'] * jac_phis['eps'][2*N+1,:]

        new_current_jac['Chi'] = \
        tot_current_derivs['dphin0'] * jac_phis['Chi'][0,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Chi'][1,:] \
        + tot_current_derivs['dphin0'] * jac_phis['Chi'][N,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Chi'][N+1,:]
        + tot_current_derivs['dphi0'] * jac_phis['Chi'][2*N,:] \
        + tot_current_derivs['dphi1'] * jac_phis['Chi'][2*N+1,:]
        new_current_jac['Chi'] = ops.index_add( new_current_jac['Chi'] , 0 , tot_current_derivs['dChi0'] )
        new_current_jac['Chi'] = ops.index_add( new_current_jac['Chi'] , 1 , tot_current_derivs['dChi1'] )

        new_current_jac['Eg'] = \
        tot_current_derivs['dphin0'] * jac_phis['Eg'][0,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Eg'][1,:] \
        + tot_current_derivs['dphin0'] * jac_phis['Eg'][N,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Eg'][N+1,:]
        + tot_current_derivs['dphi0'] * jac_phis['Eg'][2*N,:] \
        + tot_current_derivs['dphi1'] * jac_phis['Eg'][2*N+1,:]
        new_current_jac['Eg'] = ops.index_add( new_current_jac['Eg'] , 0 , tot_current_derivs['dEg0'] )
        new_current_jac['Eg'] = ops.index_add( new_current_jac['Eg'] , 1 , tot_current_derivs['dEg1'] )

        new_current_jac['Nc'] = \
        tot_current_derivs['dphin0'] * jac_phis['Nc'][0,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Nc'][1,:] \
        + tot_current_derivs['dphin0'] * jac_phis['Nc'][N,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Nc'][N+1,:]
        + tot_current_derivs['dphi0'] * jac_phis['Nc'][2*N,:] \
        + tot_current_derivs['dphi1'] * jac_phis['Nc'][2*N+1,:]
        new_current_jac['Nc'] = ops.index_add( new_current_jac['Nc'] , 0 , tot_current_derivs['dNc0'] )
        new_current_jac['Nc'] = ops.index_add( new_current_jac['Nc'] , 1 , tot_current_derivs['dNc1'] )

        new_current_jac['Nv'] = \
        tot_current_derivs['dphin0'] * jac_phis['Nv'][0,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Nv'][1,:] \
        + tot_current_derivs['dphin0'] * jac_phis['Nv'][N,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Nv'][N+1,:]
        + tot_current_derivs['dphi0'] * jac_phis['Nv'][2*N,:] \
        + tot_current_derivs['dphi1'] * jac_phis['Nv'][2*N+1,:]
        new_current_jac['Nv'] = ops.index_add( new_current_jac['Nv'] , 0 , tot_current_derivs['dNv0'] )
        new_current_jac['Nv'] = ops.index_add( new_current_jac['Nv'] , 1 , tot_current_derivs['dNv1'] )

        new_current_jac['Ndop'] = \
        tot_current_derivs['dphin0'] * jac_phis['Ndop'][0,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Ndop'][1,:] \
        + tot_current_derivs['dphin0'] * jac_phis['Ndop'][N,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Ndop'][N+1,:]
        + tot_current_derivs['dphi0'] * jac_phis['Ndop'][2*N,:] \
        + tot_current_derivs['dphi1'] * jac_phis['Ndop'][2*N+1,:]

        new_current_jac['mn'] = \
        tot_current_derivs['dphin0'] * jac_phis['mn'][0,:] \
        + tot_current_derivs['dphin1'] * jac_phis['mn'][1,:] \
        + tot_current_derivs['dphin0'] * jac_phis['mn'][N,:] \
        + tot_current_derivs['dphin1'] * jac_phis['mn'][N+1,:]
        + tot_current_derivs['dphi0'] * jac_phis['mn'][2*N,:] \
        + tot_current_derivs['dphi1'] * jac_phis['mn'][2*N+1,:]
        new_current_jac['mn'] = ops.index_add( new_current_jac['mn'] , 0 , tot_current_derivs['dmn0'] )
        new_current_jac['mn'] = ops.index_add( new_current_jac['mn'] , 1 , tot_current_derivs['dmn1'] )

        new_current_jac['mp'] = \
        tot_current_derivs['dphin0'] * jac_phis['mp'][0,:] \
        + tot_current_derivs['dphin1'] * jac_phis['mp'][1,:] \
        + tot_current_derivs['dphin0'] * jac_phis['mp'][N,:] \
        + tot_current_derivs['dphin1'] * jac_phis['mp'][N+1,:]
        + tot_current_derivs['dphi0'] * jac_phis['mp'][2*N,:] \
        + tot_current_derivs['dphi1'] * jac_phis['mp'][2*N+1,:]
        new_current_jac['mp'] = ops.index_add( new_current_jac['mp'] , 0 , tot_current_derivs['dmp0'] )
        new_current_jac['mp'] = ops.index_add( new_current_jac['mp'] , 1 , tot_current_derivs['dmp1'] )

        new_current_jac['Et'] = \
        tot_current_derivs['dphin0'] * jac_phis['Et'][0,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Et'][1,:] \
        + tot_current_derivs['dphin0'] * jac_phis['Et'][N,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Et'][N+1,:]
        + tot_current_derivs['dphi0'] * jac_phis['Et'][2*N,:] \
        + tot_current_derivs['dphi1'] * jac_phis['Et'][2*N+1,:]

        new_current_jac['tn'] = \
        tot_current_derivs['dphin0'] * jac_phis['tn'][0,:] \
        + tot_current_derivs['dphin1'] * jac_phis['tn'][1,:] \
        + tot_current_derivs['dphin0'] * jac_phis['tn'][N,:] \
        + tot_current_derivs['dphin1'] * jac_phis['tn'][N+1,:]
        + tot_current_derivs['dphi0'] * jac_phis['tn'][2*N,:] \
        + tot_current_derivs['dphi1'] * jac_phis['tn'][2*N+1,:]

        new_current_jac['tp'] = \
        tot_current_derivs['dphin0'] * jac_phis['tp'][0,:] \
        + tot_current_derivs['dphin1'] * jac_phis['tp'][1,:] \
        + tot_current_derivs['dphin0'] * jac_phis['tp'][N,:] \
        + tot_current_derivs['dphin1'] * jac_phis['tp'][N+1,:]
        + tot_current_derivs['dphi0'] * jac_phis['tp'][2*N,:] \
        + tot_current_derivs['dphi1'] * jac_phis['tp'][2*N+1,:]

        new_current_jac['Br'] = \
        tot_current_derivs['dphin0'] * jac_phis['Br'][0,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Br'][1,:] \
        + tot_current_derivs['dphin0'] * jac_phis['Br'][N,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Br'][N+1,:]
        + tot_current_derivs['dphi0'] * jac_phis['Br'][2*N,:] \
        + tot_current_derivs['dphi1'] * jac_phis['Br'][2*N+1,:]

        new_current_jac['Cn'] = \
        tot_current_derivs['dphin0'] * jac_phis['Cn'][0,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Cn'][1,:] \
        + tot_current_derivs['dphin0'] * jac_phis['Cn'][N,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Cn'][N+1,:]
        + tot_current_derivs['dphi0'] * jac_phis['Cn'][2*N,:] \
        + tot_current_derivs['dphi1'] * jac_phis['Cn'][2*N+1,:]

        new_current_jac['Cp'] = \
        tot_current_derivs['dphin0'] * jac_phis['Cp'][0,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Cp'][1,:] \
        + tot_current_derivs['dphin0'] * jac_phis['Cp'][N,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Cp'][N+1,:]
        + tot_current_derivs['dphi0'] * jac_phis['Cp'][2*N,:] \
        + tot_current_derivs['dphi1'] * jac_phis['Cp'][2*N+1,:]

        new_current_jac['Snl'] = \
        tot_current_derivs['dphin0'] * jac_phis['Snl'][0,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Snl'][1,:] \
        + tot_current_derivs['dphin0'] * jac_phis['Snl'][N,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Snl'][N+1,:]
        + tot_current_derivs['dphi0'] * jac_phis['Snl'][2*N,:] \
        + tot_current_derivs['dphi1'] * jac_phis['Snl'][2*N+1,:]

        new_current_jac['Spl'] = \
        tot_current_derivs['dphin0'] * jac_phis['Spl'][0,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Spl'][1,:] \
        + tot_current_derivs['dphin0'] * jac_phis['Spl'][N,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Spl'][N+1,:]
        + tot_current_derivs['dphi0'] * jac_phis['Spl'][2*N,:] \
        + tot_current_derivs['dphi1'] * jac_phis['Spl'][2*N+1,:]

        new_current_jac['Snr'] = \
        tot_current_derivs['dphin0'] * jac_phis['Snr'][0,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Snr'][1,:] \
        + tot_current_derivs['dphin0'] * jac_phis['Snr'][N,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Snr'][N+1,:]
        + tot_current_derivs['dphi0'] * jac_phis['Snr'][2*N,:] \
        + tot_current_derivs['dphi1'] * jac_phis['Snr'][2*N+1,:]

        new_current_jac['Spr'] = \
        tot_current_derivs['dphin0'] * jac_phis['Spr'][0,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Spr'][1,:] \
        + tot_current_derivs['dphin0'] * jac_phis['Spr'][N,:] \
        + tot_current_derivs['dphin1'] * jac_phis['Spr'][N+1,:]
        + tot_current_derivs['dphi0'] * jac_phis['Spr'][2*N,:] \
        + tot_current_derivs['dphi1'] * jac_phis['Spr'][2*N+1,:]

        new_current_jac['G'] = \
        tot_current_derivs['dphin0'] * jac_phis['G'][0,:] \
        + tot_current_derivs['dphin1'] * jac_phis['G'][1,:] \
        + tot_current_derivs['dphin0'] * jac_phis['G'][N,:] \
        + tot_current_derivs['dphin1'] * jac_phis['G'][N+1,:]
        + tot_current_derivs['dphi0'] * jac_phis['G'][2*N,:] \
        + tot_current_derivs['dphi1'] * jac_phis['G'][2*N+1,:]

        current_jac.append( new_current_jac )

        if ( len( current ) > 1 ):
            cond = ( current[-2] * current[-1] > 0 )
        iter += 1
        v = v + Vincrement
        phis = ops.index_update( sol , -1 , phi_eq[-1] + v )

    return current , current_jac
