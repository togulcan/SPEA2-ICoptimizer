*aaaa
.INC param.cir
.INC 130nm.txt

M1 N_2 Vin N_1 N_1 NFET W=W1  L=LM   
M2 N_3 Vref N_1 N_1 NFET W=W1 L=LM 
M3 N_1 N_4 Vee Vee NFET  W=W2 L=LM  
M4 N_4 N_4 Vee Vee NFET W=W3 L=LM   
M5 N_5 N_4 Vee Vee NFET W=W3 L=LM  
M6 out N_5 Vee Vee NFET W=W4 L=LM  
M7 N_2 N_2 Vdd Vdd PFET W=W5 L=LM   
M8 N_2 N_3 Vdd Vdd PFET W=W6 L=LM  
M9 N_3 N_3 Vdd Vdd PFET W=W5 L=LM   
M10 N_3 N_2 Vdd Vdd PFET W=W6 L=LM  
M11 N_4 N_2 Vdd Vdd PFET W=W7 L=LM 
M12 N_5 N_3 Vdd Vdd PFET W=W7 L=LM   
M13 out N_5 Vdd Vdd PFET W=W8 L=LM  
M14 GND GND GND GND PFET W=W7 L=LM 
M15 GND GND GND GND PFET W=W7 L=LM 
M16 GND GND GND GND PFET W=W7 L=LM 

********* Simulation Settings - Analysis section *********
*Vb N4 GND 0.1
Vreff Vref GND 0
Vp Vdd GND 1.2
Vn Vee GND -1.2
Vinput Vin GND PWL (0 -0.02 150n 0.02V)

.option OPFILE=1

.option post
.option probe

.OP 
.probe V(out) V(Vin) 

*.print tran v(Vin) v(Vref) v(out)
.tran 1n 150n 
.PARAM AREA='2*w1*lm + w2*lm + 2*w3*lm + w4*lm +2*w5*lm +2*w6*lm + 2*w7*lm +w8*lm'
.meas tran avgpower AVG power 
.MEAS RSAREA avg PAR(AREA)
.MEAS TRAN zzztemp FIND v(Vin) WHEN v(out)=0V rise=1
.MEAS TRAN offset max par('abs(zzztemp-0)')
.MEASURE TRAN tdlay TRIG V(out) VAL =-1 TD =1n 
+ TARG V(out) VAL =1 rise=1


.end

