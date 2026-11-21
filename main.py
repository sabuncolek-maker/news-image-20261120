#!/usr/bin/env python3
"""THE WORLD TODAY — Friday 20 November 2026 in one page.

Stdlib-only newspaper renderer for the make.fun news-image-20261120 entry.
No Pillow, no system fonts at runtime: glyph bitmaps (rasterised from the
DejaVu family) are embedded below as a compressed blob and blitted by hand
onto an RGB framebuffer, which is then written out as a PNG with zlib.
Running this file writes exactly one image: /output/entry.png
(falls back to ./entry.png when /output is not writable). Deterministic:
two runs produce byte-identical output. No network access.
"""
import base64
import json
import os
import struct
import zlib

W = 1024
H = 1024

PAPER = (246, 241, 230)
INK = (26, 22, 18)
RED = (178, 34, 28)
DARKRED = (140, 26, 20)
NAVY = (18, 36, 58)
TEAL = (13, 110, 120)
GRAY = (92, 85, 74)
LIGHT = (238, 231, 213)
OCEAN = (233, 238, 241)
LAND = (108, 116, 102)
WHITE = (255, 255, 255)

GLYPH_BLOB = (
    "c-pMJhqmH6w=Vc9O%WQyrd!VD7=ua1fH67VbICbJlMK(^k_;@M>fd{xaeLJmE*Z(vlr%Lp!)N*WYu8!sNb=WzU4M0Uy<h)Dl7Ic`"
    "4^WE!>(>bV{D1xWum8pT1s?x?{rca3{j%Yo$iL{nsK122eibJxW(6<gBG+a;K>+Az4i)?FU$7jD%b|b2qy;A?KvvxLr8&yC!)!mS"
    "lm5$(ssZqCvDaJl2BkpPruq}`e{yZ=yC^XA#UKIz@7)fvcXI`QuWvyr<zE7(5*pwlmvgF|S!&l=5?25+wya#Qg-aRKm;*M(<Hq>E"
    "NPt@-*SJ_=wVW;%;-Gv=%w3cUfE_p{M!~iNLN2JENBwjQ05<6j#Y06ei0?dpGVhgzcAMOHerf@L@t_oH%L&^e0d5Tb2fIdkkFF*t"
    "6nqnMz0J32r=Gj7M}^2Tw<gzW@^VgV@X>Ulxt-k8Y*aWUaE&8zv*iNiowEm+gTAz%&N~VI%&OsRwpUE1=lgbTF-xs<zuu%!!>;cU"
    "jW;%SI;~v*pvEP>*Wy)FZ|hQ(H4Qi6zvh5}Q<P7LcjsCvd;omPOaPB#AJqF<CsPX92u{ijj!pei;oUXOmcF6J{%_bAjc1p{vn%>i"
    "=x6tXU#P#B$3SzF1K^GqA5i@Z6J)6vOJ><c7+>%$%$QyQx7>SiVN?t8RSP+7H})Vh(7k{vuC9;~Y#c0nhAhF^5nr5GK&2*a5UHfS"
    "WO7^Dqgp($77mXG2me7*SOKx;tuQNW4k{T|$V|+0Hg4kd#$`H!@7~xIu3P^sx2*-y^IkljB&0!rY=d})nmwoIw-nK9E=Q0N{n5WK"
    "hbsQ-(LEC2Mf3}#jCt3oolu_dk;kL1|MjaEToN|)`~UM;btD=Um_ekY=;#0UQJjXw{fI_dhttgoHUNBuGZ5H-4J7)T3s|{t=j7C0"
    "x=f<pw2g>uJs0#mcv~2VXP7?kcI@dUVJArE@=|T)2h?I7=Xf{WouP48Qz>(;0likAH|@6>*K{6FlOd6ujp1UL$?bJ6?m`ulxMIW`"
    "EUMTUtejai3M=(4whmrbBnvAU%^)B0g!Yk<SKu&4OjHT=qK?DV^|;W|nBV-nXevbQFyrQczn29dJME)I=v}#n9(mmsR0lb#1mJoh"
    "Z3|T05miTjb(WuNVTYlV=%tiuiymR_o&w+=?h!d<Gws~RQ45h?!qqfUin|`7h9WSw^c>0;jg~7pW{fIkzA8rY$)qm&88GunGL?;#"
    "?U&9rAA%HC&OqntTKvQZFP>30cCh3dH}@hwK3MA#7eN)XUlnI^uAV8J(iNB7>ye1gp3=$l3;1YVmyg*)4LzNj$3t5VrSk2PcX0(2"
    "Kg(iCDbpzdOK0wzV#2vG)q_%=O2Kv+K3S%sq9Z*3%yHOkk@m|(>1d5;X2>j(*F$NjxkEFx(+}*5X`!5xudSOtXrPMu&x!@g+-J><"
    "D}ab4%UeS`!J*_=1>DV4dczh`hBO!{<sl%4qcYB@6$h;<>Rz=_@RL}q3SSiaW43`ujI~#-*umv#u~KK2b)*_2_z*ubHQ#l}^u3#Q"
    "A=@>E;<d&afl_7L$X&*y#JZfmb8Bx;RZ+$MuZo5Cs(W^2NJ$QKeA;0Viy)drjY+0%e!4P|IN)E!rsK+D8$h(qTI{WJ1$1)>%ki0d"
    "$XNQ;sN(;6ELj$=SSWvtTk}$T>=s<DhDwN!)yv|>p&ZcW&l1nSQ>GO3Qdk}Z9`Xn+D9+k30XM&0DY$bcS<zFH+QUYucm>yMfrhDE"
    "3#R}u3WDfKJDb)M3xQ=&b<(3cw6vfE{}5o0zn|aG1HsSsjborh<6_}%!?v#u2xkS|ZDzq_1gF-sd5Eoq{rAbXN`$4VaWs1@egah&"
    "dK1rZ+*K;HDb>&2o(?WSNkm*R#yeFxmaRJB$VUA5QQxIH5PnFMw!$5Aw2Zc0(%N>(=O$lSc^at=8_{Ct2FrPuSE@P4#Z_Y}j%uAa"
    "m4b~F-Jk@L)0n@V({1;~YM1Jn$x=D#FjhcK*xB*9J3Lc#T+BK2yV(THqGBJNJvAsLSTFxJQxtFxBg?etuJ+Y)0+8KPv2`2Yr;qN2"
    "A$<ZSPk6|Pb8MzJGbbpsuN6tl$!^%mYS`G(O#!f-L?j;y8eyQ=_E9Psibko~b|IPiveqpGdrT2-f6@H0J@-P6NwmwTi3o0je2!=+"
    "z6>u`eWIHLG`DC5L)XZLkl<LD`dR?!c6nZOMo>u7t`54LpRU1*VQMb%j;f1(Q@p$<TYC`e0(E(5(JP&FMb+x$Wa&|IOqt+RF*V3e"
    "aSG-RkJjL*p+J+)v?T}R=y<keb}9qZMC?T||Dc%c?++KI6ORt!<5swLvLQxjuWPa&3S)Y=M0Dmrgd0@iQR*<+&O%W?SrBUhrLNm^"
    "K_MvCQN{7s_VXGFmkEw3C#J@#1PC>ksc-M*^R|-vEqCX4pz0LNtFPS*S9b^$<jV6Y3Y87h)}uL9%l%|vI#DHwmwxsf&t|-x+w>D?"
    "Jg@Y!PBQP~nbD>{BbzKJ)a)^yOhf~!+uf$q>;x*OCn4R=$A(+fg!(z27CG5cfWkxsip|yx(R5TUE3t%nxA>bP<06!A0*^PM<V)Sd"
    "N`FvhMysz2Dwe{<d?eOKtTl*-;U6v=9n_79W2SL?%ogd_?7h0tIPG_KPds)$8lcb^EL_LKy$y0%4)1dy#O&fzYq)ci<gzM``Lh{o"
    "GGfUBwga@+JaRwd^V`J#{jJ3oSdq&-B;sR6Ly@5}1QE493i0>p9cb6yJ$P+-Z>mg9?!lmAd0neQ0;Voh)MH=K?qJYx#Ri^5_5@Se"
    "7!oP!PYN}mf2|OIWUhj&Q@n}7IdqUVC4%>|?M^8cz4FeQ(2h2O!Q-t;D?1M#&g$A37IBvWec79^2)hMJXq-e9XTPllqET;W#Y`PG"
    "E$89{PmJ>AI4B7Brde#Xh7AYW4aR^awZ&txlZPou0>=d{(VS}v%#NK=%k9uA5O-7dWvfP{@24qhEcd+}7q@JopjLBatrU*qkqt>^"
    "&qi_-6Gu{@P|U_o#Xn60sxJRVyZ=S|wch=qy-)}j$`9I4bJq{;IWn7SAlirE7|ZN1?GD|QN@3cAn=RN-cEUewJG@R0ZjmI^cEoD9"
    "@VmS!6q~1oFCHDbI$UQkgiI)Odx-0bxl=j~kf?CxjlS0rkFJRlr4{{9vEh`S#h46z8={Jf-`dTI9N25KQnwXLFUFf1$UV$jP+L}d"
    "1w&CFU8DWMGYDH!f{;#CUo^1OH1$Y=QR~2soT%awuGshDQ7Ra?3P>Z)V2fLt-&VH&lN4&B{JBvu3T=Zbxu4GdeTo(@2bfCwvmn=="
    "<^gqc=0GxkOR~2`O#xJ6MuyInas)L|`E25pIk@34CT^8N(3z<Ko+_89+4NokYSC2!ialFq2De@T?xUA-wUQqc(B4|IH(cI4+HcRn"
    ">9Xki*@ICN)ei*%HZt0%MloyeZ|YDn(|E#_KF1x6gmW(|aaH3vVLIDg=KywrYvved;+O@|uABj}RxiGc2aKL!+S?gzunC$VDpn`q"
    "tXdni4%&f8%Hk-9q*caS^(A-BwwlG0Rr~BESF7J9Am&r1K-k8|>aJ9UtBwtAJ!4m-fvBg~!byZ1IMrPe(R645d6k=PeLepasPo1Y"
    "R?r^jTTb^F2sRa)D)moB+dIa}7|g}YC2*iO(^JHl#9X1{73qqkDQgQJ?l7d!(#ipw+*pfHxv-<$ClfS2X|Kdv*$CWSvzS)^Jy1o<"
    "v$GqH*T_{u_6>29g32c4ZZM<%Fb+)(a%rikO!H)=2JwK_e<`5<>&@6jn+u~vO9T_^rp<qIL4~nn>c2m2W^4;%s~FqI*iyD^W^6rU"
    "JKD0SX&v|Uf4>}H*u(Qn?zvWhjpw)x6|)g2xz*{}{J6EdP4<kQY`*pj9;w{0Mu)QM$IpREm-gQlsuZRfkIQIHuc&kjZ&q;WlGtqp"
    "EtP`C6-|AGx7zkYeMUYK<U^P$G_<ii5_X_;9<$6oTp!uMV0Bbkdkv7OZVAK!dcssBwi?kku9fD#`y`vJvAyQeL*ebd`;gbjaDhW)"
    "nGtZ!T5RyVWopu7BxKFVa<dOj(hew6xIS~erSr+7Y=rDgX0!#SA8Z}DGiJWtgXSk$T(w}DTr?|`mbqFYw=LV@cu|3v#RZp@iBo6i"
    "yrE#NuK(!PgDi`he9(iebIN?)dRt;Pk~#_`=b-25Vag7FHI)1^nq@g*x5;QTPihMUpR>?iVZ&<h8ZF);OV756+1b8yrzD>(kR^-@"
    "w$kJ28F_lpHqx?|V%zK$z0C&Ztl`UT#bWX}HlTBzUIy88R0SI9ey^!-;O?Ng!^jFwVY=(sf_H8e(tKo~x<+p^XqmgWa(5M?yJ<Pg"
    "Z}Lkz$#BBql*WA%iX%6etvtd}T=$OHF%lo`>z=cj>0I&tGX8fHT9i~zqhy8?hncvG-=VfHoUb^y*>UzEX~NEY++sePe5!@5b1Oi$"
    "F7%%Ixu9axKd6On^0A@e)E_UdJJeg`luGta9#qZjp}qZmCul$p1>Su%jS>NG**doL%t$!m!MVeep!r~7re-@DsM`6X6BPUhtNo(i"
    "x}006<igq_NIbugQ%t{u4`|$$lA_|t;2WfGIv(p`D7@(UJPO%60lPs`@IsL!qOTax&q~R$x~I!fHx<aFhLybKV|E_v!W0IoEqC5b"
    "2XxyrHm+uTEwnhke|;bS=X9XwS6>V)@XgG{-#NDBRFQ8ubdNBCBa;M-ZaU%qw@bzZGUxY?jBZ5ERz$}*vcP)x`i%|&bq}mC9a|=|"
    "K9SbKUX@*FosU?w?00b4JG+vvspr3D168;A;$dsag+N1_HFLYif;=1^JPemBHBa~Qd%SwT);6kc`v@qokcsdpxr-|^d@(Oq^K^~j"
    "_J1zuf!(LLp&}bO;Jf$xPAFtoO4O^ln{+b44jQ3h47(J{!G+=|U7M>3Ryy{tjRISJkQx)QWeZ-oM%dJ+qiFl?2IMm%gxvtH=(HQ@"
    "_X0N?b}t=1MKRmWR!wqcpSRE=HJ`UVbUWfe_TD^>s|m+cnnsV<i*0<)?Vud4#JGAnK9V%v&8%Ei7oTIVGX`!Zg-E<HPWb^DXPkX;"
    "7VU$C1H>PbaeU~^57w<g#b#}iCQ++;`((Tyaq@AGt2N&E)8u66Uq|KJI_26dh>Wwd1b(?c28o7qjMiDcP>2eoU`@*Dle}2uUK<Zf"
    "_TI1@rN&;ov9E2pICAEt`x2SnEP*oJ1JPjGEw?hVU2Fz+mYv_~fn(k4Oxj_->=KHSwvDDHM!_*DPlrAhuBSjNbH2Nw{=`R#bnp^%"
    "f^fIEMPtveWX4MadZNwAro7`&#g|VeK+YM(Wc-N$;P=Tks?Lj;U}mcX<uSjDmEmuU9XXBtA@uz9&5>=1E=E((urCv}Onu$#-1b1>"
    "&uVvV&nh|qk&2~|w`$%H1#&H<_3+rGO6tKnUS{T71Pz7UR_T&${^v^;mA`$Fu&%WTG!R4{ds*P_6Ocfg5IT^yY-8Oa??$RA?E)>f"
    "$Ay@fqYwFYoh$*BUCIw`xPLnTUQR4huP?cFRJvv_gQUl11cHeeX2btJ0MPk%phK}13$^;;Hqe^2=E&X<R_&8Qp>RhhLM>*ZV5ux1"
    "w(LN?f0f4cVtEEd*QJdHS$NjoCI30z@{duLKRPaP?fhfVxsUkCe;+77(hn99(D>q*i?`7_zp|O9VIW}7;-kPLF1akc$_X!VVMTS~"
    "-IeW1)?WGkw`qs@>yVReKQk%nv9}@N1}B7p=5r(4Ni#ZQKY`A(Sf}?j17te33mKKua^0R*^@>(V)={^S73#1Q6l7s6kTxDYwnkwc"
    "v!=*Mp;_|k$;iG!s}g_IPLb4O22kDPyG!`j|GwS+vZBS*Pqdi&m(gPO(P_B3D)wn00x#Zh)JF{KI6kA;C$E69<($Do;29+Ax1Y;1"
    "W{g9t%p<gFO*YX|_SU@9%@Z*wlqMpGsGXEGMTq%;y6d;3^zGz8+;U*2%Pdkq?CIAmLUW3q`#|cZVy8Yhm{rdnpy<Ohe*E;Tq7{qc"
    "y>3Xnx7FS*D6dBYAUxOYW^QcbX6`}9V=zbnjSQh*6>#BEi#@cb6<b@%8b@B9hca0oF8rwKCv^NWL6Hg>&$bNCeoAMSad#@`2|JV<"
    "AS+3z*iaq<@P&Y9+HFW4zyzK8WYQr>OfrbKYA$|j+s@>wk?W#$9hnuTeRH(d=oBE`BO=4L@)Kjq-TaH)KA-e4(w;}c5V<_afm{ua"
    "zeCDacrkdF*j%21h18r{6$BSH)0+On^lo{<)x|mV@cByN=+Ud*`R+b?Ai$*DRy{;dSW-cWk9gOc!-=>nQ@X2*qXD3Y{gixw;(NOL"
    "3@=j_FQjXfXApgcm|3i@(binV)@i?#5po<z^{e>+6>4Zor!KUi)t=7Qb^cTgZ1T}UZ}AK*zd!9DD`oKz?18o)fIbxE$z*L<@-zIb"
    "xxLX;D%p)0sxNr6Cg``2GIfJF^l4h?B+V)4ar<c1wQbehj)^l?TSU!SC+tbh3WD8tdxn%D=UOooOU99nQHQ_J|CBo0bvlWBHRZoA"
    "_ghREN%TZ^emUkTPusHSo^fTtiYwRb!|?F8xH4SOr<||a{f;bK`yNT&QK$fEKT{Hr)g;pPpwX!o+$5=a2Ou3E<j851Vn~l$JAr3>"
    "S$N1R#6V<ECIhzAskLG}gukhP>^RkQt`;kWNI*WN#Z7|sWmX^z^^2?Nq2l$cVVhe;A|AfUyO+letffs$%#3&jnx9J(wr~h`?bZsO"
    "I~rXm2ieT@-`=7PY;K0V&(QNb;ld@DaA!<ozQ0Ge&6d6CD<N)Q6t4CZ6yMH+1KWk?)+zuO$7rCE>(x})&FlrJE$gy^{BHj6dNQg)"
    "X+uAw(eEv=lhocj-jtn-R-W!Q;~}uXE+QNgBk3OM6|38?E}~IK+vwgmpbN;hC5?61J<n6SHob)d7an>R8Q~e0es2K<#G3nV5US`<"
    "gFHoyal9aI8Y|R)yFW^pGDu_sv7S3*Pr667dFvFpq-t11w$6OE38Fz@`DI`c+cQ4>-a;x*giWmlyoR}xa9BTF7B>pQY1G@Tg0aH;"
    "PqZ?e91gf5gHeOX8$|KLm|VHh=JgEKxm0oNJPec1K=nr-=<-1}*8yktyqXNl8z)mKPjg%t0C7B!0^w;nqDAH)9FUqvld*4FRjzm~"
    "=4y$W-_aZt^Fl2&gPR3$vj<rt@{Cx&wSeZ0G4)j(Tl$gasGz_BqC1u!3#2<HPF1gz^9EUf8D1VC`*HJ({=YnAAv-%i?I7W+4-BP`"
    "q{g~mv-`loCw8ZlfjE3V)9*r`N!4y7pt*x&MnYwmccu)N4u7+pp+#@DVF#tlj$VXn3&5R5X3%DFtN*)&^l<Kr?8gVsn(oD$gY7y5"
    "8SoaKRwMyV0mmoFU@tY$64!*O7#(MHRdNlznB6+N`lQTd;_eY()qUU`1DE$;HfII1mn<Fb;(p`QdoY`O1hbI<S~BMOF+N}NDDW-`"
    "pV4ek>t~Q}KBW6(M{HQX1utd(yq{%Z>R7}nnA^(v<UP}SJh7;BpV4ewA8%>2AF}iD_w(B`oc&J0CKM*?xEw#(tg5pzC?cx`XtiSS"
    "{z#F1PlZ<#)$+{fjO&|F>M;o4@oY2){pi`Y;Tj=7@1KmvxR|3pFU^2Amxk6Fqc0Jwu{+l)Rr#Uu2)5!90R)zhYH?hfvUDEmp?m<~"
    "IS!Ietx+De5f2(vaTi;2n><77P$r)reU7!r2*{{}XMEgU55p+jhxuz+FS%7mY%q+3;#B-z-MWXap1U=S$P6p2487z^A8idt@l^(y"
    "hL4!+*VNi8rQ2x`_Uj+;1Xd8TUE4{pU2Y;`9?-rVy`g-ks5<(eA@7Iw0NE?#xq7jFP;KqSfi;PP3mF!ktLQ?vPos1SaHFdoXy-Cy"
    "A9n0RQBS0rl-icYMiwjUU^0{Pf|MK;Px*SrjobuhGW!__$IAifu~i#iGIFIwDP_9jwj+(A%1e+rXiJ8!R>D}-4W$pt6&7I<^3Zcb"
    "%bdCtXP4!MDko-3RHQ?MhJ)|eIPMx{7F*@`kO$$LGr>339+gfs>Q=8(>yl{gNx4&MOMLwX%T*pYf(Y-7aZYosz+XYRRn{l`GfMsp"
    "Gg{r56&#HTe<ZZVP0DZO#uBBLfK656RtoSo`H|v0#Pc_&{3;hksQ`R7KSLcWIT{Vpct+0O_EXCSP&Qf1@%gN2vV60%!c7#8`cJvZ"
    "@iT(Xe^*Oh(~1B1AQ3qM?vJ_FE%=P7KUj<k=`DJ+M4*NvU5y`Z)q|dyYL$^zvz*D;S!6kv$eGOpG-*`Nxk-mLEnebO>{(luKCVq`"
    "^=zt7nM`?zYR<Ok^DRxTpOJR|8;fC@`~#UQEs74lI9HMDADWh)<17|NpxEWZn%X$%|6Jrzi}Vb+Ge4FSp^e9}-!6@3)SY>`SFwb^"
    "WA$$?(gf661$JFiZqhUKF1+y?qA24wGi#W-59HL;ekQbDv#g0nl_1L1qQ&AwcRaOrNFoy=vGT(bT4$;3*Q+g$Y9ZVww=%%>@x^BR"
    "^bE(pGsPe0`Cs1R(T&xfVR<asA6!B7E^EjTJXugqBsOyzbjz7bR(wX%ruBX2e5a7k1-L-o-5wF?H8IWZCE=zVO;!npv*r~RR!xu)"
    "M;DMEW^VbrD|AOr>LHO{G=@k{G?mUXTK~=!-EL+9=X1~sm2$yGaoWt*WWrX7JH6+PYt~$CV?=tnxBEMnxt_m^r41~iH=#&4A7GJH"
    "5GaOS#*GMMQ1}kpTl$bTZ38l4z?7RU=8S;oN_LMO%<%LmNZKC^&vrc)!((7of3gl++josV*q?<NrcunzaxuQLLL#WVY!|v+o3+w%"
    "zc1j-mO=47x>lLt+31a`*&@1~qg;JQ9u3z&E#UW1zQwv$hf=4X4!M;vH+a&>JO9|BsL-)Eaar9|PmjWq+iZYaHw!zI=a7SR(Kf(c"
    "dqTF8EOrEAA?)m~PTvv!XE%4HNXG{E1;VlF$KuG#mUiK-!>^?Z9n5)`OM(oP7JXu(N0}HZLV3aRR$c*8SG-n-<E;7&^?&I7wx!KC"
    "zE|qOvZ>g5w6QiREoJ8c$w=eqbfyjfQ?x6g3VFnvZ0C}#tgz?rE^RuxgU&!11{}#%PU^*5Uon5oB+r<C6ky2%a!FzN48ByBFZ`Md"
    "uW1W&(HeUn8UMQQ6AAFf|IJa-zXZ`<sE07H=k6q?VUbrk+sHifd_<P7A~o#F?T6JE#{K&ihWDn?Ig?nB-KI{vn?c(r5CC`Wv<VPU"
    "&!)TwvKH9jEt{I=&D<I))QeWjDQpHSlItI86?%JsI)!TwG`58izN=!vz1lw%ki8@Q@E}cMmJ8)wTY13)D9bm41#&+OP79!STNkvm"
    "Zc>?PeZk-N>m#5JwiT6De2ao_pgMp*Bdwv`Fka4&=aL&J0d@^yHf`ZfZc7Bnl%h+(NAC7Ovm|d=S0}IlBs=cyuG3hrH;o&Rae0Po"
    "l({1n<mCzifO%F4ww+&_e7=zU#tlHqn23}j0J#Egz`IHwknoalm9TCRGK&YTmy;Qi11!SAQEbS&)=Zdi>`sLx-2|ju4hY5CngD9Q"
    "5&&Vxg~*ksX%QK>?oR{(ZtO_&0}*h|rcbz09xolQ%3ctjZHQ?q?t%=$Ewzx?=*Qul3fYEHLjkBa_W7ICH>v<O24@D`5z=n=;7Gfk"
    "v7m-yiNvWWv7PBiw2}7<E0>|M!*C>LKczIlT{x?-u;)c9)z$C0GO`G`C%)kM#tM=}ZK_Py{BUTNAU~LDEjyQw|9<P%MxEbq1;}H9"
    "ogmm9f*m8+MS`6rmfHk7P_Qe-a;lKz{fRDkCxYk&`-6_Ub8fcx4WWZ5Ddm2<wdLH~`x9aC*!muheR7qQwjH$ySdmC)T;)+B?QIub"
    "fQeG}Pm}>;d3_&Fik-ju12eGvWz=84#+p#mXP46_$biQNAJn7@jzh<HMIg|Uw-)Q5*ax+VP6xqEyL1^Gquwjb)V&EZ7%D_<CcOys"
    "<W3ao2jUZTAUxu`XaJ>+afZTLNLdp5d7F-U>J+0&UcTOP9gFQ1!VL6qCzXqw;;dVblnT0NImmb}y<FyrK6pmr5WSQyz<P;{JG2^3"
    "M{0s84M!M_VwtPfEnw>~x1Rvim5X{~lP3y6z+wK^%S0%acfVL<PUEpYN|F2Vx!UT>$C5IH9H3|O_eM_%PBUTRNVXSfw<7IhS87Tj"
    "bMHc?tEFt7>W9bi+Hovx((!L-0;YL#WW^rgyW2h9yUiP$`90uzEoRq~-pqO32E{~zW;@vPPdOr+=D4ywT#s9jiE3Qu8>4`Ur`L0P"
    "H_Mb<u$~fEjRdzC7&-w-585d?{HhRzGS<rB=(cGe8BeH!@SqV_$+&X1<EgqhdS|tByzN`Y+o<x$n7G$(a7a@{)f^AIAjQ<}-oV)d"
    "i_Fu0=WI%sp)Kl~qHt9eM92nLiAmE^gb;(bi~^oGhJV8%0^#uN8xo<j8)CWiz+H#2X*hR42f}b-na20+H=Y5C8<DwnG?C>hqqhrl"
    "`yJ9iVV%4E)GTo7?=J$A1aw^<By+YE`2;uc|J*Zp%U;`2X>;bz$*VjJh^Jg9Es1hgMY&_56-&3J&2j7RT%C<IpgDKy8{~kh|L)c6"
    "^1?Y#*fm0;SCM{67hiF|N^GU=alD;o1U_tIl%A?|q@5=`JY0<3qNA!?s0y<tq>?^cgS(3eJ*~FeptmyqlredNAA|?!05x^)ReL+o"
    "m{b0;e^9^;jGE5wALs0G>-Yviprt}L)qzK~NlT(_-s8<7n+`&=WY(MtF_}eALwQj@jX<IqnR)aC6>Adxar44tgNDV|>o>yijGQIg"
    "V5v+(ba+qs57NO_JLPUgrwc`~s?S^ZDqL6vcGCIg8!x?jEcQKp@92onWwQvM@Urp9+&OiPg>(}wo7i*NWJ>BjQSE?KX6EqDMy|v)"
    "CY5++N^NDv=L(!_z}&Roh0!;30*~>$QI$O5Q%Bk#j!S9da%C`uKbLR(1RBwpBTqqzy;37`cd=F2!3g<pNWV?rxbdq}(S0vFZwXb7"
    "PSb2`oY=QFPaFmNz)>KLH(N3hpqGaiE<&05BBTdOnwWdffJ#*2yc}<w$NFRr1fRUCpPz7wH*UF-&4xDX`KO4(!rIquv!9A+8>#Ou"
    ")471BuI9E1xtX)yunJgD&$S75fims5TU?tHr2KAhEGI#Cf;Q(mP|08eP^I)xR^(D1q}D4p9^SIrqz6Cv3LKk!u9-@mYHQwRuCxk}"
    "lT#lUwc7#E7by+0X<u$>KhlJuIzm*(TWb-uoSE-|usCq~1)#WL*C%YVViq<b_oW9_K0$@M9IwqEymR`bJ~CV8387&2iK;D@1C#sC"
    "w>JirbOg~To4lYTpwfL>1~%=PyfW0|VYf?*Th?VSw@cbL`~op!cXTj1K)LSDO=qU2hSH>?-!M8pFWMo?AT<a>QYPbFyLuk#Al`~v"
    ";Lg~nV8?I7E}D+ImqK1X92be2DVFy=h`)TYRdHSI()iso09wu?e&1sr9J?L8VYhe&f)IfUHrZ1Y;dYx_fKc`DL}q*jWl1NCBQuN3"
    "kcOH)$5~4Kp>lL)0A-3$xnvgO3wugxfX>Cmx7=6Z#ie5IkOAUvbLrpE8c@*pZ1qCxKVF`Ajd#L^;q1b4AP0<O6~Vu+R$I2-rlKLJ"
    "{~3cN;@#aE4j1b<<7knscj;zch12-iVYqf~ykR)7uJ;Y%pb}S|pbGm-Xg5gPHmOVH+=+aEI6k97a<5s8OmvXQ3A_eoHPLBE5$x7j"
    "=Fa0m+p-^{ChNmav4^AVc*8GTtZ)%zyg5vLmH$9<{8Om&9|N3!bliWyIry)z<rkoXdjvZpDU<hoB04Aw(Lw!`u&@BTu>J+<c!i-e"
    "m2H~5a*01eI$(a!6KT?p_Ur@I!Q&ZX@eGNj<(10SMpKij$F@zAJbxfNKBk2#hMVQulv3)~{yv^Jm-mG@@Vh~#txn)b%WbGguW^WQ"
    "f`+DIS<TZJK>LxiTUzdv8bXH0o5p$f0r9}oB3Rn~`_R5H9`p~!gMMN>n19B2FxV>pMFri_wn;}NF}=(bmS9(ux3Y3lp;mfbizxR4"
    "?!n-Hzb>9scl336VLr%*Gw=ECesP{|*(~qFuCuOoQtMv-0`w*yZaNZ2;yIHMC{2(B7aKXTx-D1x*&$qTehxf}%(fGMcA0lNnvF&k"
    "_@ha->vA1<w3RX-S<AAIwe|#npzYI=HB<y4_(9`1*qL7cZV#r};4FHEE2OJoWx3K@+N<dO*BqY$oBpH>w%b(QqlEoa+ktGv<EL3F"
    "G4m~L4pL<R*L4N0z(Aeo1mEBwuh0)-iinLp>XGYKJRELQMlfZ$B&81{=WdszKzbM&(9LfC;N>~8nDOUQ?VOah&8>IdK$OYb_4M5p"
    "zf@Ku%lzf4ByU^HHcAQKZu<dM%?j5&ep9q%h;_lUNGUC3v2SgHu@0;*m6K6;B13+lI2OZhD$T;EhhObwo9Q_p?JY8w1|Zpv`z^rb"
    "s!I8Xmg08o;7;4?w4h172{)yRpwAkOoN)K`e1Km}GUaJbs5x$3!RGdW{0NY@<*uC-<#B6pc)~;&JS~*PL%M&2FTVjrkcQ5a$FQTC"
    "n(s*G&b2ygvqrQUxg{i!_Ahs%UHBRePAjQ+jt%XY->@REg5w&bMUOr2Ph=F<Q3DZfv(Fb!++GTnsx^?PsViSMyE}uxor=A~MVJRJ"
    "7uxu748|En``)UN<OTk6AG>eJVpRjt@$gh3&(2n&b<`bzX2wtKruVr9m{%kXWZU=h*}}XF)U5JQ{HVkBX@r2Fm0H_NY!I_Mma2bW"
    "_`T*ISP6-E-jZ-WV!tCi-6y03sdat}HdhMn13Vl30F_ww#;;XHstNC)5(YhDg)*r{vY;@Lpz3YAx`XR14bt0{2G?p3ZhLexjbB7T"
    "7>Ghh+^!R8Z}Xf6if~Dz7?<``rk^+y<{6Kx#=Fg{C!Pecg3AyxgX|GxD>oA`gI1gC<S4krgkvb&wBIC{3QIq~{glJc^6gj>ijk_?"
    "Z)MY^^gHB)u|zdeR?ZK9R5E7;^|JP`gj1o%U{aUB-xslfsruCQjy`#`05}5J18%yyJtu&AB#N#83dE9mU&%d%nirR_eBX^CJBRx="
    "9ikQcHnHq0+HsH2tjS2w-Rv?-v>G+_t@w^Uc@7vY_oG4E&C3CW^AY~QHRyV}*ajB8!cs$lYPuUSlUpawC55CJCLYXmYX?XrOrOHB"
    "?HHEMO`}p|<W=5*D6iQ;7E{TU@L^eg>d9#v+V#2ED9<wh)bmAw3hE+=CH5Vhin(kBD}}iXZPNP(>!Wh7)DI@*H9O0=JLxus%*{Vv"
    "B#w6E(V0FF35D`p^aQR;Y`M7Xp+0_r*?!$uMf6@$#>UiqlV$=eIe)gS+3d3|vv|j(yt+fB=vE=9M*)|0IN5O$%KCKIuofrT>^Seu"
    "`*{R7`%xV;#mdo5C#fD(lZB!LGIu)-fZCNn<l<d2B-1^?8SBKG&}5Z<;3==}$USl9h5MFuZi2%`&H6eZ^&*8Et2(kv8oyM6w;RCj"
    "k5<O&L`n?OZrQxihXN<E@zUS$lxKISM*r3%-BBAzCd~tLjIsxy3oHScN`L@yJ*zN=yoVM=c~&;l=}H7>4Qfr_Z?+X@-^69KiUL3n"
    "EWNZ*BHVy+ZU;?cBdG64l~-f73nd?-BN=Ey$tK8Rc_|o^Nf7chWx|bMg;LxMXg;S~Se5QmKo8fsAf-*b5B@BKuOOPJXEbQa2LN3)"
    ">RvVK5x+qz$jI}#7f&I_WI@ko|G}+Tg@oS<Eo_2w`~s{z-~HfU+ID(+>ZRM8dhA}%>LXV>GjomU`vnvV;gA{2o~^fB`02pyU99KX"
    "k+t#V?fvekKh|1Sn1PW!FANKbm0CaA&b}l!`0bAjzI4|43)1pN<8*XiK7bX>J|cT(xnkdXkXie;HiGL}?^$sBfdgqD{=kOOq8T=^"
    "vvJ;8y$(%Vmh2{Xqv-J+<-+6nvrsPn<*Dl2MU!e|*(x%)wvNu1L%`1p4Wxd~Ba4Bj)9;$8{SV<I10eJRa|*npTxd(3pkFAL#$q_B"
    "vBpM<m^e}%aGX2@H!Y+a0BSsjkG(rE>XbD~T%~j#H-c^tKfkXN_B1!9M+ws_-K(^{ZCe!*OtLc*!$JF;1v(eb29wNS1}!iLK^>f7"
    "-!7gQt!(}w>+@WC_MYqDuN(pA(e|I?9S_*<#eSq(iuoVI>hN&w{E9drf}WTcKkmnKrzZO*S33HwQ<eh0y(L%mOKiyCSMEX5bB^`T"
    "L?sTj01+Au;XYimOy4@zsw{4FA~ve^Mj64A0%G1SLYnM!-{1~o2_xs`iznvA|05?(z56C24s6NlOm8;2^75R*Z=9+#Z)><9%cal+"
    "6^WZM4-th$N?}_{?jxB%rkX`Xx`47LaYaR9L80e<VqQMFMz$`Y*h-pF!O&Ei(x;$p9GA<fh3XAqopWST*}H}FOE2>F2grq4k+Bzo"
    "X!j7xXheFIrkl=qy(+5N78=O6nRW0<>}j(+T1HfHzIpx@1F4fgK;9zdaGsLG*6Z3Ud(C^cPS)U~XYEv=p)>+yshdiSD|ivPOfWAN"
    "9)+`x6D-_IP7YpeifZP4(vFW?Y#IL)zSfB8^O5;Dxr3WNc6CIDbzX~AWJ=WksfhK;)e{%<SWi}7f?8Q(`$7D(4l9>wrHDV~TDLD;"
    "%tJkYPFBbWP861oEXG}RdYr39<&-=f{_|w{n@ipVGGk3vCLYRnt;yocK0<e%A|j>R=@6><81${HS=D#~V;+-*CH#XbUI_d{${Lkj"
    "c>Hglcn8Tamc#y32&XQ;UFZ*x4D)i><AM8E7ZEi`fLb<C+iMXz^F+${zxqjchhY<@PJ+W17wo436ZC9ptx29LKH7l;%ct(>fk`|S"
    ")KCe(L<FBWH)Pejnc!M_QnAcg{fulY+&fa{$%v1srsDsZ%l<_XYshEY7ifljUt}#FnuX+c+T2g`=)ED*=^i+)oLC(joltu_7Dmf#"
    "Iao8tJ>isd?g@_Jv_^A3ny<FO(_xjhmBb<7HWeP~ymafag;5vhDd+HEP-v*xc!Fj=IHuP`W;dU9o;vMa&r0Rb<*k*<5$uSDCZG)K"
    "k%ggaM&)2i>@-~h9D7vvo+yNlI28%f&XLugQi(H90L{1I>X(}QrjBi5sTFWEKzY2YH^5p6BexyNx6hS=M>VEiD0(|g6t0i6g-jFs"
    "Zm|5x0PAc5E9U%_IyBSm1UI;s69sfG1(j?y8}z0Ke$X^uf`zi51A{c2EZ0gN>N^xgt@(4C;Lr{CoePb)ikit>;SN=JdrC`&r@Q|!"
    "<u72(Pd^_%3#+5qkB*LeKOMbN?vd}$9W`2uSBCI5G}UY}{OD-@mV0!RAOf#VQ<H49XyNIaJO<Li%M)nxzI@;au<o^SnxS6Y8YLHS"
    "S^c>#67=J@`NqIJ+YZ-H9yB2S{j|RA;&N=a%PH0qF))o<DYBXfzhiEmS|<~3W@OsgJpz4J^f8&GA@Ju#+-DKF+S_v2Aq%LsvTLt`"
    "4a;52Y@uEM4DpGK5VD0DOj{D;K;W8^d_Lq$Pxy^sNt!SCjb#fa8^`D9aQ@dgQPe78pIQ{`2cyg*<6jqk!f)PJk{G^Lkvg7||82@U"
    "38^U6l}~$+Yy&FYYZuxzw&|ZP4H<+};jR=>GSm}_^QI3Nye)~eF-n^s5<3hR?Ou;^R&7v@d3Mt5*~~##7ur;^xx4~OvdO?--CS{W"
    "dDV}WEgzBYEIM<RUIg-f-JbUZ5$}*alj}LcZ%~|<vIv`Qw537_M0{R9KDkaGn;vLTa+$^WT<O%?6;O3oM%ok<v|gq<-a060Bg^dA"
    "<4+v7KwG;c5H6ZxpBvVS`HFaiyDQ0-Vz%nW==tYT3!@o5L05}{3QI{c#5x}a3BiNhWP(qsUWQQdrCR1Re{CNO)u?SOI%}T;L?z;C"
    "1R=w&4Ai+6Y0ckLlLdt~I=ap2>rYcOly!=Yys$(T$s#goMQ)HFkc+I-VJV!^1p&?-7No|-@<d@=`CLRx1U(8QA-0P5pAellcHetr"
    "E!c3@40D{{5dl$mRDilsA(CK@MYz71CX2(yXzO1(^n0oL!D4@tdO~#GdYMr`-g3akJm)#Wy*FkDjXWXkPY|4;*?5M*5rO;)D}-dC"
    "IgHk^S>kRHn>Ob0LFl@gVPIa`mkReSkUeq&WpK^;`)_a^xS@-An{v^k%(4jdR&6NqekuIN+bodz55&&X9p#Ozqfh4&mBWjk!Cohz"
    "26iuZ6i}Ovafr73RDg-#-}=~r1@vt9HxLhnyzH3`pUj2SM6=-y)&a+@r+>WN-%{5Xj_0`>GnO6UG5vdKfa4>f+&z!h8cBvyvZ2Vy"
    "s4pdLccn7mT^jib>tR1(J>lRxtcSKv52@Yu_8AE0&*3MqN5F4#SdsKpp78s;r5-XR{TuJ7yR?o?+TPb<y=f1d3V+TBMbIyY+3UIG"
    "8jA~otVq&MKRWbJV2|ZJcbU;S4j%O^KqBC)51&jXWm+jWc^<@F`kh{c7B)RB50#D|$2w}XlSL=R*7k04(kDSia>YYho@HcWG>zDE"
    "lYGHieNVX0vlrw%Hj=??W;Y@_!&aqzwuenqz+Lj^$8ossp=F&JP9nxs=LJ5qh}#l(disg`5ndK5a-!NM|B#~WN`{b~ITECuo<(HT"
    "@<T1WIxzsRxv2C!+}Z$olG{9fi=JV*TW}sxYH%%3*IFJw`$Pj-6Jv$c$Pzh{%MLvck~_zeF^0#CzYuN0*~uSk2my)CE%D3#>%#u<"
    "9whCT4Xrmp5RhG|)-)7P?1>6upQs?*wKeY{BD*1AJg&73pE5M>3dPAWeo2H!omhs)@Fg6PvR<WAMDg`Lot5#94MG&-;EmOvTNf^$"
    "n`?sm7zv){2i))UoD8h3v3UIkv_x}ejRhTFlsp<kvyUzKelUQ)AjFi)B1r%Wa$q15*bP5%LjMDftMQ!2d$@VU>Vy`h;3$S9)lL;!"
    "KCg&kR})+d6?7>kszotD8sXVML5M7#=%H7n7<SfC@99%yIZPe(X_fuCJOM;MpnV*^g$3We4fysSF6l9#oM}&L6;ZlR6w&{%->Asm"
    "@H=kq(&~1Y0+T+ozR~asmsa*_(4tq5y3Cy`$o3oFeQB|2RC!J~!`+%?lfwOpEn=S7BJ@t}XK&vxy%)TQ#x6G!IlF$jsRf-S#Mn`l"
    "_t{z4XPci=vbjm*rIIIzKzTVkJsl_5@jjakV`+)rubbk|LAjZjg2Xv?Lp`+P!w^;l)z6~S2{1GIX8JqM=phgO&!>C!wHm2L-wg7@"
    "iwM&5`^i6FHO~=^b-DmUL_O)b)H$JAZSc2~1OEonhr0pGT`z#z?#W<-qUCqs5%&ON{2$4}k9q!Jg%1?c&jS7bLs<R2Kzv6eaTsy}"
    "ySUCpinDSm2>I{Svd9eX1A;}h)rkl1KA}nP!ad?W6E@o<S!{Pmvo<k`tx&vQa!wHpl5;v*ee4^eN)j6r$NnX$LZxsy^Pb}OhwA*q"
    "C@~L=l16y(`a+y`yP5hXR(2k9jp=&^psM&)A%k7D3BXmoinZMxJ~=H=zTSpVF0WNhJSHR8TUayDu|P$((@z<I7RZTr$Q*`=TCC~b"
    "x78DIz0ozP1&;f*6;CrhIjwF^`7@xmIXml==_82wJa&*2_!C%X;uoj_^iG=hR)aQnK4ol{Dh0PU#_4MkLH7iE!idOvFnWQONL;hE"
    "67%hCbUNyQa9h1)NZYj}nT9t}FC`Dbu6s}!`$D<hbuGh{!Vt6E#-_%Ycs?_O<8jM$cHLz*u%`4AHD4afKq(s*miEjksdiQn<K_=~"
    ">8(4$J~4`bgjb3HzFdoxNA^@00d+VzkSw5cU4ls~%mK2Ov_unmXyHvqk+h`s!&+i74TD&r7Jj0b-kG^}G}>ptFf%6;ThtApkW~UG"
    "f%Jiz^@?7=EHB$q07YQ{=h@ifWDS}=H0QV)z5$|Kbs=;_3RxvmG0PTd0Af)ZTLU29I}Be?zRM>!>V4fNn)-Zz+;rs78QL%B&~#ei"
    "W#N@JT1N$J@`P_If$D-j!0v(qR&6aL^ar#F`>H@*Yi`w=I}fT7dJW&Of)w?gR$2klC@45G7q|v4&}uCVEqlAGR^%N*U0UyLRBN;A"
    "0-<{L{%bH>A;+;%=r@EDjXvoRbB_Mz68;V3M4<!!s(I}H4;x%M1*H-*x0d|iEZS!1Z6cS|s#^4@DB$gk_j|rszuS>ksIVoZM){L-"
    "0?0n<9o^+z+O#UZuujj=$UD{vkic=z`Fw?rtGZ!#sG?gWXe(uZ!#n*19}|Q$T@;sS6tA%fQG?X6d+*cAPKuASr=kVP)Tg@y!aBcf"
    "@ZVA>(z<xT<$s`0&oGSepThO*=^4FQV(sh?5%@p;eFuF$;84O>!2JUb<+tEaRtPoa{)9u(xB%Xke?5b&QSf+c=r=$VW5EHU(d%>)"
    "XdHe6L_PA0tI%k5iKIUOQNly)BeTX&cncA&QqatpqMuEDbqJJZS(oiMSk!Cw$jUG{>h`OE+6PX&&09Rc<!>Fm^*r{cE0lqj-38u$"
    "Bg4rlh;>kK5^n@fVB;HO6p|vl(@>P#)jknYBpyrTpZbWx{a~cJB=`YIfj=FDL;t6PaPaH#%lK)<m|$nd{4RcqQEzS&?6aAu`1bV_"
    "3p0z(15%ixs!5!nOZ#-d@Mq7iCphZ)dd%a<q+FrfQSb*vZbHi0f*Tgu$|EcklBu_B+&|#-=W8_n4xl2Dw6X8_G$7PRS|~ZOr@lX!"
    "VsS8KIjwt1T@*ZxP^3M&JJL-+Nrc{NR%j0pvL<EfMYRrh$GBvY!FjAr)uz_DwGQ2-mVf^`3ZywY*bX|#a6n6<C@P&~>flzg%ju#c"
    "7W*-0w1d!?MY*Z37LLijnZeG0l_%OdEDjFI(If-s`r4#oNhC&k$RZC82u1onz6KA^(04J@``8ho>zuQ7sf+#4_3PSs#E!kVr_Of0"
    "+>RUAO6jX0w6pQ57qDh~#S~BF6@T8(2j0`D6>n!km7jBJ!1E(FaGG+P>pedhSemi>Wmj3B=OC-$0f-LOBgl+^$i(lPW;h#*n9Qi*"
    "y@HG<83a+Hae<pgV)%nVdOc5j?du_kdj}W5<)RWG+2ak$6Opn~Tpd0i_jXUX+!KKG<RT0};!`7_<Wl~W;`NW)ZO74R&+D1Z)IO^?"
    "j42Ps)MEBT96euy#3M&9tnChj9i)}2R*C))<Sw)qaZ>v~7Xk0*(+H2_Y4WB#xcWeJU}-qM*WnTPc$)4yUsK<aL=U-kO%tBo_vtj4"
    "KiNSJitI`TaAz(HltxPjdh@6y?yF8_oW2(_9)<I3-=93;F)FOZI(I#(+AK6PBRMuoCF-^K;aKA7@(x6{$8E(k);fLF$2gk%bY(0L"
    "oL<o#>n$J1Z}RQUSRT2d>^|hB0TT-{%MkJMf4sG%6TSHS+6g8MZ7f4q*0)R|C887*E4&-f34%spB+bjnt3DKlbPwSH<+D&i=bw?%"
    "21_db{QbQX9-nM7xw=<15gog=?McDh$quST)oY!Em8ssGc-Ix%9dz<1sWR<Kw9A{BB6@ZH`#UF?D@cmNpCh5XiSw<i-wSEGVE7CW"
    "E|Kv(<=p0xOLPx+xb+xq`EB&RT?GicbKa_u{i+aiQ=(c-%K6Y1sSlL5P42Rm(>>}<ge~0S?%D%LbT<^)9ctUn%&d2}D&)Q@q_%4l"
    "9Z2JIDveAUK|r@Y5a{=TKO3E~2Gw<GNkClcHD)&m%nqP*rEOcv-p<^-R)zd$g%8O&8=@ILhXZRTwC`fwAl4puDNq&Bi`YwL*pC<!"
    "u!@Q}MkAS#WAX%k`;G~sFnX-s#K_Rzf&F$}u6NZtKKF*_BLi*Iv8k7riPXAoUu~)`v1CSPgO*9t%X&a27zq@<zh8nX49^_vOE(*<"
    "Ts?An@9C5kx!813sxlGMah_^w7Z5Y&Vc)%YWze@f?x%<`i<{|Yz+qAN{@oH5^0VHVqfh^sx~LbwzgmKXihg&YEOfRHECkyA={}_P"
    "pO~3vl<RTE3zN$pD^iSFYMaF(d4#HXq{e}?t|+-nR3-t_5yen>bwOZ-=<RUpJ%KUSOCR{$<Oc?79%?^dOrCl%+vm<t6wF(z_K53<"
    "kFzeghjpexX7vsezpliUN`<zu$*$AhH(IB%GsoqY*>1ilZvSwg3o?x;@A5JaZURnf4A46X@tfHTE`4D$+Bv&k>RHJ2hbIjnBs=+c"
    "Y|CrQvy_<4O78AwIOJiIs=Qpw9h%`enNAalV0W?Xi-m1%3$ih8f4xm)GCz~K5YJya#{Rw<8X#NIjwXHc%*ga2RSr6Z5rukFla4o{"
    ")0pn>=zUU$Av?KT<qzK<!E2Y{N+wB0;VR>2>eZ8>4Ybj*Cx<ejKw|2q^Y^pwMo+?N)700icqJ~n??9mgrtO{(dO)zdx<7}ly!a2j"
    "Ynu*TfKfM-{J>*|eKntRk&Fd<dP3Nl`gWjkcB8tBM?!l67U{RHA)CzxGhBMA`NWxgtYLmOZQaYRxR)VLhg3M%(N?ai9a@25!_w7D"
    "i(DFGmi^vp__S5MH+yyN3&!sQ&(BvzUR_5N#wE8uK0t(=l1;Af#3TW~!V*@BEl%8z-)gGYDz|dfoaos^(7$Vpf4(yE*>zJ_11joQ"
    "9g9`xg4xyql^(*3O|EX$iL|qyB5x8~dHdkiPld^~imQ1(j30@--G1ag;UDjlP4V498<av7Iv$CinAx%vf@7Aq)=z&LPl|BIt-9cE"
    "s*J>QnU1I9E4tY6?x9BMShWjtx9#TxBX2{A+Jt-L?$0Sq{w`ek`*J@(4)9cuQKn=j1$F0K<^1&9?c%o+PcV!yJ=p!tr8L`sZu)SY"
    "X(r?RIp*ZEAJMp+U%*r?E=~7#*ygbUnQRZO1Jn<Epf3E4sa%~tR}MW9bcuRS!q2j`qJ#hW!pIv-{661LmKa#^`+s1G%(ub}sZo*l"
    "RlQtIrBpOE<#Lr>@l6X>G})F|zvqZEj;t?huE|>^$=MIHFx<3S63#Hh;r<TNt4$eZOv@O7cs1icUmJN}DXJg%**h$GN}{iG<ZG}M"
    ";!+K+h&g<E?w2ZL5j8Mf%a=;ez%};OknF}ON^}OpPt?T+L$-HPvpk+dMkCL0_Ha(83k6oO0jjrgbeju=k`r9+pWo<sN>os}44`9T"
    "yJ@uK?$5C#pG#1t{hl6@J`Gbz<_gXQ%S=VmNa<+T7px-XePsMSB`@5>`&W;Cr!@7V$_^>rI1!};{LOzxzj^85EEqxMDv(l7^Louh"
    "tCm_Ur7HEGGe$n-Q95V~FCB;#j9GJ(x?!d$Tu(G!CdNEX#Mjnxibs4V`pvZ*F?9u(qY?!x=vVxboRQ7KC)X0h!HjXE$zGTIyG!_N"
    "myqv%VP<yd+m;|pobBoaEM$F6ne4cF2@U&96kLB!5_wgKVto>nV`Lu0HwTM-C)8%Kv%b{Ho-;JuSH!jDEc-6<{i%@G@<{g8-QTBZ"
    "kyx)l@;+aJ%*K!eGg^Y0w9`3lQb{B5{ecizvF)C79zfU?K2+k;c?;6AV@vxw{#9hr%Pisc)|wAp)yo8Jc~jr+*6pKha9~E32<pnv"
    "MeH&7{j(sj>V;}|)kpSnQ&H^8N!j$1gJWA4w;Pl7M)Swf{m^b7Yp0k{u2zgpoXCfD$03sfiKI<-$8ALuEB<hZ@^%n!g?7l<QZ@Aj"
    "xMl5g^jVhg6Fp#?Wwlk3nVxqb1GOoJ)^?qf0ePa1W^6r_(NQ)v6A)koXuj*a&g?N21j(g5uHN&lZgWY?WI)?Be@^dsoDG9`WPVyj"
    ";bUW&v!Bboz=jBr_>I2GC>7eTJLDB=Vw}#2#k3Fm(Ay7P7J0}h*XDT;$L_p)dP5tZOw%b)w*u54&<Q+bBx3TarqY9|1HZ6lnrca@"
    "L8EslAmduNZsRCq#@zQ<1X|Mme|=iP=w$|fBxs-9{^<hC{dO`3T+^PoNvE+<n79wi8a5OylMx$_AYa$f@j}_3NdBvBr2j)}L@?;T"
    "zu<DuK)&$y$qzEx>ZUc`a2|Xvy%(L15=GYKy7{fs8Cs9lNYZ+z1`opZ`i$7KKi~U^xpkWlPE1kx{@w>`eRWZB<~?&3P~BA}0&U-!"
    "nHih)>Nq;i#JWVqG&8QB4}Dl?S-_ErDbxX*SOYUUb)gfEdjspOL;RiHjD1AL6eg6ev-VNcjAgS>9#y)1g2<n*{fzFFVUa2I{izQY"
    "iK4M)H|h2IysZ=_{!xdVA#}LAxw#zkJcxLw#KQ{ie^O*2%JWw{M#L0MMm)B$w>)<?9AoTxK%zHra-~OmlPQ$5CKEihX1S`J{3-H%"
    "lm?<G8Wp{+*0G&1BQafS_WZ1YhdZP1sjPJZQ#9%dpkw~O56-|JGq^Ix#+{ffsKrc@U1E_7;WOhw?o`r|Nup!(6=pC!xn_&$pI`N`"
    "1oX%im_b8EZkmx$kT)4Q*VkS9NH*sg)K^SH-RGV~u&pysm}IJ;n3?_cap2PUe>Q*DD-Y+-%+7;djWMGEQZU)edAtzEH?~;pCUZz1"
    "%m18&0k9kQQL)Xclc@wVkK1`Vvj~ZR`8W{c_32+!(7IUYx!3K-MFV^&SuNxpp3ToO82_q6!Hj>EO##>;P<Cu*Z9f`+0vFlp6Z49T"
    "(9Zif_j3TocZZ%m_(O*lA20MnjzIy%Njq1p-3Z0y9T0Ik=CAp5-5Kxa6Qy0=-M*Nydb_?5XM)pD_p&RP!RKLy@Ax>GZu!ZBF@-A)"
    "+FCt6H&a7pVbbzAzw``p!p~gb0ciYxw7uuD@;tLGdMzwM5f*jih`q_dWK52y%H*6(4i;Sdkz|_*Jo63TUhB*svxFrF<yQCT9`r^1"
    "4sk(-a9;7c!d!ZR_N{GDYd|0t+?PDpP%>#d%NGY$5Z|OD=$N?sq4#)=KJxbN)-|2LYyko&*2Rb_+@85Zqu_e*xkN2!6p5^--_8F;"
    "@SzXq831cMoY5W;_Ooa>SI0#GrqOWTjQ4CiG$@!w$Z-Cg&OcUR{6Oy2KEYjm;u6sz(YtZ?2PN_$#<2JfQh}GgZHOIe&)VZK@6W5_"
    "6dMzok@>8&OlKN?75jPfmz4iIDh2-dO3_=ud@%*A#y|(vEq#P3*REh>2<`@sv~yLg-1d{#gY-qF5)GGzp;=jhQO}uzEFGWCZXGu("
    "r>gTN$8GCnkn;PjsP4P(_!H>%UGvOkR%?;>K+#@kUL9rY+}{r^vGp#+hFs+VlGFE78xElL&E|n_M-p4w0mTzlxyMFSX4*c7s!(t>"
    ";}>fs5SiB$UvziP&UnuS4h0~p^)*O|r`3-+mjC&bs&cqHLPHy!n4g}s6Gz?cM25~`9PNpAx3z08tNlZ9a`EmCvG33ks2%sUPCB!Z"
    "wsi}P&hEpDyWTH`4sc<^ZgQ4Lr&=82fM!+VHAT7X3ykJrK)9$px_`!pK;MJmqcV{#Grf*90sJ&1iHB`T@mTYXuC8Fz>9w?12p!#q"
    "52oX%_c>f;m+ERef<EuLJj?}8eG9#)qPLE<ZB@B0-8e%|ap86q-7x{)=eteRjF)p;%B{<9|K15Yj2By|pareZg;pO)bdn!(?kbyA"
    "?gv!y*=FQ@j;Q8#bmIe%k1fUFI@K&2cbJyWH(l4u6)h3SUP8-yZ&+TWx(>@&$E5v1%b}}wl!m5d7Dzzd<_W*M7m5$x4Dhq^4N02J"
    "6Zo8Q-JT<lvgtZeS(42!TKuqL{+$WnN9i`3MlH{&qx@FnH@(~+G#u{={g<JVBUXSPB97tu(@qI=v;z1d;t-?11Z^OuhIEZ>$L_bP"
    "l-C>h%})8U+W`5|rNY;=HSXhorQ~4IS*4!Lr_s??d7#(2Azz;^<S$+hgJw~;#Mxt^ly!%izrE|1+4!l)%v^LA&41q+2x9%LhZ`i<"
    "#O$_@%3TJP6F0<0bZ;^=mpr!*o8$`-^rirPw?|Sx_DJeKBIY3b;Xuu+aVScA`>@fT-*cg37A+5KyfM64AF1E?Ih46KbN~5gnj=3r"
    "MFAz*Lqn%d4Y5o(HXS`uLpEGev_~wL-qX8D7psV{G<aWuz_@e(e0OUjz3RCoDqDX?2*rr&Ol-~h;``^?_4o<NppSYpE`*l^4wUcV"
    "eHqPaC4HrG4>zD!*JQ9?sP;fk9%P|B=4(_-TuCrHZmvKof0<i2Z8OtK;{ySVIgLPsTx<I)F$b!em}d`u;k=WcMIizg?r7bj0jbbm"
    "<Fkt->^*rVv{Ek|V7TYfO0Vz9pIOnW`yTOb`I^U(a{RQk*D{K`STD#R{kU#s4}X_l<$~L_w{A;PmQ$JyeFR)!Ufd@v{nWHVodnU&"
    "!d$g#YN6*No6e+-Dx*Pp9@tazwg=Po)H$Llo7{C6+6{|KwdhT1d$ykAeUvRDRCbRNZf7Kt_n6Y1TONGBP;n^p;0X1&{nNZ@awG8@"
    "FQx7_mf^Z!%|pP>I$rG&ZBWJd42|%9u8)P{12H{qhtQn|e9Gq|UP}Ih`f2ghA4#qAN|+2pG;+p1BuCXkptvZv&?b^-;Gp&sRKv3v"
    "Oh51aXi<ulKzv(?qBh8xTu1Mu9UQS0<}EmIfBHBS{Zk;#cJp#QolK&ip_!5U3cK)0NK_GW>$b!8Tk3<F=x@rs8$(5XWdTJH^njw+"
    "b8#_$fiK=Qjd~BT;4?tlNO*~pfA5x2Q4h@MFCUvD?LmJVNA(!N4BA|{0Q$H0tblJVZ9s~r*FbfI*6Bwhv7RZV(#E}zqnl6C4qXMt"
    "#%in3tt`($q<*%xto_wJ@5ek6e)lBQvJUn<DAxx(N}YV5Jev7X?l??xL1gW=qdT@1%t@ezX|L|BN_|q5V>gd7-)}~9fvplz(9R)V"
    "{^{p%K_YivzS%kiohY*$7%t;j$FQwIArV5G6RRDF?3&$PgLQ1*Olab5BeDZ~4Z}x-7>rjAcEHT5O@f#BCh5RU;mdmHkk8c(ZI;}0"
    "1*56#0#J@+83!tHL0PTE$)<Yt*8+qVnTDzMtS{2^ayN;$)9Y^4&eNaV93~w+^+ZQa>}|#DVp@4^MYCsf@+(#<9HhPRE+DBsI%C{P"
    "3R@V-;g;B%_1vG-H#rA>MZv;NiRkTWxsq7^rl;g|iZx%OUL{&0PTq;Fqt+xIxmTD?NOL6e&%rho9h5csNX<VvIgD=~Yk6(oJ8yv0"
    "4bjYECdD{MiqoA*Gn%VGD~|)%=NAo7%^b%2q^JdFA}BNQFvxc7=S(FY)BrtqCc{l{<_}U1;pJ4aOOQZOL6}IU0~opzB|av@b&gw*"
    "xUP_iuWU%{IO_PfTPGO7*7MHLd+z&B-&`E{+oRdiBElvgS4|1#c$hq7K~PziavRBg8lyM1cfM=9MVITM%@3uRpMv>aSMWCFr~76t"
    "!F`u$_M+bu97I3hQ&R!aH(B;nb(?^k)s<eS14Gp!>?bv@>={l$tW<Y6(r1l?X*<B=+#Ur?kyf+C>~7GLpHl48981it*0QA?GYofF"
    "cWwOqG|cLth&&bc=>LBH^lMS*1U=EgC9R+UOiQh~)R}A?qBCYI0=igmYT;NYtajG^eJr22bx_K!MisBx26U_8(ZaMNXxxztlud)}"
    "8@=4e+W0F)Tj=xsms)+J2MMZ8l3~Yq8HL!sckf^AwmIH5@15&#FjQ+3-eVsJR`K4YHo8=Q<>Ejsfuob{?tOpY0!D05z<!HQ$kSuq"
    "Cg0^dHpTegnuwWKNQ*ULW@a6}EV!@j-w-z12Tzkf`#FatlHq)8Bgf?J9jEYAp6ShOeGgswqW=jfmo+zXW|}iwu{W7y7ngHpDtO9u"
    "Q0NcuR&BAMK%(q-2ljI7$(1^;ifz&Cq;X6*Cu>P*g`i!!2LTOS)<kko2kU7FML-R%)!sqGaaO>4(1DlSg^uY^8WBGUN<{*IQx887"
    "*w(l@p+l8pioFHXE3pRBZifa6ZMOobt(DV(Zr0(=hC{LLyU%nZqR*<_cF%p2YoM2D<+D5JS@gGE?J-KFAXUxJ_)$Kdjr#|5A04AD"
    "A+5X_)$ZK9l-C}^(G|u)<-!jvSG6U~Z&FXoOyqA)4N{9j%-sV|M-QZngRofhkK9S?Zl#CNXmj@N<SX@)i|+`DwL=CiWR0A^S3P8y"
    "Zzc`>+i!M9{dVr+Pef-#Mq+R(P30EKl%zmfJ({W8efpVe-f_M;oM5QIZ~hFUc_54*tTwWN=}!WJ2C>i^`}z52uD$^!|5qMIetz?1"
    "kT%Y1w{F8ZKpQ1@3Z6HNFgxWu#eLXwt2{_B2weyA)6iJ6jmCQ$uk)!Eq)XHaN}KG&rc|pmB?@jwmwLJapBx!RYva!;f>8eV6s{Rs"
    "4|e}l&P;uhWH81nrjqtpb<(`G@fdvl{IVRIGOOM`i8LCVL!-^g&p`Uu49yysKwr&oK$<&wrBUrY62N;s2Qu_0QEI${nV#3KmG_~O"
    "GZi}Aa6K2i$Wd85ZbFqqKT2uko%qxQYY*T%*zWb3A|o<ga5)05Z>Ee_Q~p&)|MRFSya&}I&pXY~(Z#a1M}~{4v;6dQ;;=x&n<Lis"
    "RgrX77rO4v`iL2|tXj#_TENVlTcX13t$k~(JEX7<tqlb_A)PJ^XnW<86~kzsy>`VLk%C%aS29v{>8__r!EifS2ca=~kHdZGSOpfP"
    "<P0n@>;R?m(0|~%1)K^sq;B5&O^ZRswM)wM4v&I_jwCf<&MxG6DAc5E!F4<6SmiwPJxop7Sr8p6op#ID9pR&R!Xk8Pd#Wf8>@e1#"
    "Z7^y{s7mWHe$bs#P(s4VBKPjR|F!}~Jbvr7hgLulYjp+;-yevfrL0mRp1BW6rz_s%Q~+cw{q&77(tabu0IzBU6S22yti1NSS&gCk"
    "szwV{BRnM4xX0GQ1{@AqD~#ne2a;0l3#H}UQ?$iGrC|1!h#EoP0-n8zDjzm&O7D{a!(1cX0jDw=k`?dLtNENF8ByLdT~6uO%6rR|"
    "%wI)XI~VBMt^{*~nTM1+g<7dKNu_S<$o7*0Ltp9n$OUvy-Exmft#?j7nBIjF(<Y%VCZX|?H;ZQ>Lcm;<Fp|k;y2zV;E-tQEJku>n"
    "!zR!B%91}CX>@JpA1D0RD-6r^AzH!y4}Jni{-312$u7(}84Ee{67J&@%&QkG-*5F#VJRPc0H(J~n?-Ux?Kw|`VRo6F48ylpeA!#3"
    "+ubKCx85D=jlpa^aK|hX(yRUaDPMYEH0Z>CD4uNHcB62F(b-_VKc|v$@3Y4FfbZfHvudBHk%XHTnEUI75&kltbEA$cO>992Z4smX"
    "<h4MrTWE_1WT)}m5v!>bB>A499Mg6_Y|vLQDh5vP`R)x%kzF9OIe71K-76i+a$S&G^q6kimdG@uu(t}L^kEO_)HUqxcuEvGS}E33"
    "eS(f5ZH(|>PIqoAA)!Nz^PgsKQuC^E-j9Lko{p(vZO)As>}iH$Az6Y!>zM6p=TsdC{f%OI-V`MKF}57c7Up|QV_b|pHQ$!R2ZKK0"
    "q-nQ%TZBnVB%aF!8j~L{d9oE48kLYeWyf@COB^Ej+P%hsqj$7-(?tJZQ9B;peSpf8M$P-J+9zy=3n(vZePb3il{f(y>Oqg?MTY&#"
    "_$IXwu;)y-7{g;z50JE8#3LlO1`FlQbd0BF6(+T43Q&ps&i|NW5I}M0C7}bVYO|xW$C>BB=;+gAuJ3Xr_Me=nEpce=Q5>slhcKND"
    "m)T@AKSZAw8U96v5{E4K!-_8c_kXz;600i?(vN~~MU)A;T7f7Sh^j$XIxt}UX-e0>iNp*>t6+Re7DWp^6s8!KghV*rTlnjYS^4(V"
    "bYQ6RwzCjrIqTS5rssPG#3KzZ%*`^Mc5UXLin(oZ`r{T4u%8S6GO$DO@#7Q!vam<j`DY#-#<}G;*#$lzRVo4ujFM~YjZnBk{@D?N"
    "EBo-e7*5u9n#)E(zx*6`tXe0Qyi8g_4(ghU!J8AgNB}S{hY17wC4~_`S+(0DNUT^k>dm1ESm=UG>={C-tYV~oa>*Tcaq!J}fj^qx"
    "#$7Odo}2>JT|e6|KWtqBcEM}IE}ljS!eD8sHrAtWrVG)uMU<Z-J@ANDYC#eU0xBJU2^-I2!NipH6gspm-iOid{SFK5tTekd>^EiH"
    "@`QYI81I1SN%TW`fBQDdlP`=cy1{{<#Jgoy&cVcSp=03!okvmCQQ+RtMfVlUkGQ@96Yg&Zc0#J;Z;RgNtl-RO?qX7V1Z@}meHl=&"
    "&<?EdnEGzVwF6~Ximsuj?l3aG`7DTvfI8aI_ugw-Vcw0QDy0&r!6FuAwcJ~=hWnY2EW1?ac^f9{(&J%=g?bSkh*#Z+BW-tEdYYXQ"
    "f1J`^&H3tQ)M1VCk^s@%onUxrz(w~_m2_;<s%mYtpHipZ$#?gmBHdBfQn6pLQPQhFrM#~Ec%bV>Zv72zN`E*y<2sC=P1fNaMw=CU"
    "=Z7acZPLf#!umgb2Y&th^Pe3@cnZ}*6<Yi>-~X%OjZ*zXWwApkPZUb)nh({OO&-<Bibuoy7!GabnvB1D-mPaM0=c6oG!ES#zw__f"
    "zE$tH+OEyBJc)F`>tLCp)*S~U-QMMLhw@Mez{188gyP9&^Ox<9nxz)Ll-Db_T?M?4@&Iuvdjwj`dNP&x#8XwPHW9UQC5@J8E)C<0"
    "A9wTD$kr!jZXNQXz3)1J*+|=q<k+X$?SRweqbI98>9QWReD^Xpc~X7VE)^Iv+Y8$73liF9<#=D)p`B?T8bwgb873)|n@x~h;2Q!a"
    ";H+P-KfdMq;{@}w{_j?p-@5dh*n-TTYQTl(PhBf?Jghl?f_G(gyxIZ9T_5JE5sNosy^_nAKV)HX1#o;`&HITC;D4HwfBHL+Q%fBB"
    "*i__a5}Ds*{CsyBH}0pS!SoF#`cq{=os-1Fmv+xJu^P;sCQE`l3Xd+~Ei43{*>A)Eu2?ZJ@Su;&Tj=%SjMo<t1VgEa=RIQ?JZVo$"
    "soCPy{`AK={539OAqV58)XgOg)AoD^=6$vVk}#X?pz4Xu0j08GcA7h+`r4_+4+=aThk5=RK!Dk6o8jYKtWfd<Ce&F8`Yd~wGT@^P"
    "E*|%;<~5j|0=ia{AiYapK_>5;gWq^7(33{~aeL*q483Ui?OnFp$y^rm%%NYU3MXM0azw{A?YYknVN$x@EJw%S24WV6+;87`Y3(0J"
    "i%1>{T6@ppQTwK<Ku@pb9t&onEz^wJc}VI-@)TsZHN|3)-rj=+wvq=+?{nExTP!+-jRhVZ#lB$%0)`p*1NW#p?Np%@3)CThQl?!?"
    "D%@fg%X)GZ8poFeFaas(*n>pX5Z#)NQN4w`=CI>^L+u-Gz?;%oE)zV^Q)Z4N$YPH1_-wm5>Y8J$z9{b2ghc{xCx>@mZIieM$vf_c"
    "=4i(1p;XNk#!@(LYvu&g!AeuLR!O`?9}m-%tq4FRrc-AqR|N-95tt2eldk#g;piXE*=TXzR!7m=@Bdowe%a>ds8-QJP5@`(ScOGB"
    "LPkt?nF@w+viUY~;flm4PYv&8WSf<ALJsVmfjyN2o;ckvn(zei7tRT)VDmV`@zo)D8?6KKHV{fBj=yqFkmET$$aQaQxeH2shiI1y"
    "FnhuDkQ7}d^OZn<VAi?aik0k<sF$nyPA2licQuyzKq~x$o$ep4bH8e(zYq(57}`F(t9?3Xflx^VSD&B-isTcG%LmuQ+V)qd1p%zM"
    "SnpEKEPq8U5DPrkmrOySE9T;9)x!V5I>G5q)|9lGxv1N)O+(I~!*7kU`$vNce>quusW)pB=-QW$G=VTGjy#n?f}(FTBdx`FoJs`B"
    "syz!hsObd0`n8;GfW|hzl2+T`5nH^gH!pS17d~(dqCwJ4z1s!efeiEykb(XWfea#c({kC0FcYoT>?fH!q*~dLUx#%IhkFg>TED;y"
    "#J}1Tye=3~9@QJ#v*nq~qvYvDKJn?gg~uV~cvN)i(5SuMn`y~(7)Yu1O7B(rF5f^;UFGz(2T=2A?3pb!anSR%(eZ>{o(n`kUU}*("
    "lS|!8!BQ*LKrO9J!_p}441JJK=;uW<@Kl)KAaL}t32s0Z<e|4puF?7EO1yZ4a1Io0Z6t#44@cm8&ar1`6bJZ?);*88lPG?|hw&g-"
    "W&Bf@rfoto|J##asShR!ll+n%dU`Evk*_MFfh@OK%`^7W;{}BYdd91CJi5~$ki!H=OL9FHwXW-J^m|>AXBm^U>9O5%OZR!Wzu7G$"
    "QU&MQK5l`2C3?p?MXK#g@?&m)J7L5c#ifx<Uud~(iq10b_{F_$<Lox=3H?0nn0L=63A~WGznGwz>+ne#%<Ji!MS+==a|s3Y=#9)J"
    "h2Au5gGRcZ(%AT{?M!=GiE~!#7q>`2+$<)5kr}4@lv8<an0{xXFi;Ynpv~6w1W%tl6oz=67=-GqOU|rY*8bjlkq*OfKvo|}+PP%`"
    "NnIw|D$;IoK?fJz*0=bM#wR0%{wRBZK9p<gBA78=|L6pA5sw=?H$*^^>Gg0*!Ph(}cX~$Um^r!Q8x=t;eoT?VVPay<C%3QrHjiY_"
    "+HAI|Zc{i|XW2kJU!7fR>6+bJr(T>CpZq>FeT|(7X~iF@52l~LDQBW12nZe+@QC~{RRj4|p-gR4iCIRQ3$=H6gg`u1bsnjTSWKg3"
    "PBsw|xUndpuiQ43&RvbXABco$1pw|G9#?)6$M5V*1-eW+Au2#v6cjWfcO=-O9mo6eXjN2pzP;5VKu&ieUlbH3B|KFt-MjnA&52D&"
    "NOq=9iKzSt<UyJ*6-%67o1itLwP=n~$qVY>umxRvPRTW+T(VKZ_eNvOK`@1%XX*ALA@?VKf*d6Yj7legOI2Jgod{X7z?L3YBI-G!"
    "U7hPV|GtP$l^}0IpO6Z@I=*Pq73L@DCOsZasqs|G>X0UG)X^hTf*cZ%h@CO%7UpXl(NV6#)Z|`8GL+2PioM4Kq%zhLF@6|i6b3e*"
    "`Fa^w@=n9;;Kc$`Im>304iEH+Dx6ghp&1uPi*yOKJl~1JykFjuYjyuLFft;j1ctWcF3W_g$~Ic2d<s;9&P-?d4ZSdy^e}<@V$4I&"
    "Nb#(46E-(55O1CJDm1#ZgrlQuBdNZ&oyJINpqASW;*3e&O0NB+K0z4z%W_f!&4WESpj35ea0tAm8iGQLRuayHM@toB)Tgk628~a_"
    "!Vq)@heXk3S@#_qaP!$WFhh@Q?5XtVHX24^QH)_!Obw`&hwk<n&xkHZx0XD+(74Z)d8WHP#zM|84J2P>NM|kgDNa>DBAAS$+<6Uv"
    "iBRuW>do9IM1#C6O^0`6i%FVcaiqR6$m~Jl02fz;{zTLRo96F?`+)8nW0UF~dN+ED<Y8{>$D_FisH=k`6o8+w4I_ZBeLw1gO==9}"
    "@!~4(7WO-nNzqM^o2<yc2D;X10hZbOpq#Hp*^zU%_E93W%~T||29o1ki?gquR{nAh+5qp$JG;lg!u1K|Ft|}%x13Vev<xE+C#7sr"
    "Tt)N#ldXdGH}|-7n>>do<)M9SSvX~jv04N0lNJoD?wr*CT|}Wqur+<{kZE9|+@?P<*I8-*&x@LoIKCdro=1fU<S)tk0R?-uHjqt-"
    "2WLP$@TX<yZcYF9^`~dVK^e$-buJ#JzUqs`;&au;X8^H}gHdhTHrc-1=SJD#@?bf5z|ET5>s82&s`J&MlR03)VAHXwzT?4UQD3kx"
    "@(N(ccFa4m*kAFug}%OJmuvTFBgl+9wQO5P&M8VO0mU-h=|l{^QkK1=YauVXc0A#7s}Ac3&vv=lf(73s6~^j_9XAH<%yxhy$uv9K"
    "Dc8w?SZAHaGMry4@2W^3;O)6pF1WFPQqfZXXi7Q=!6q=qt4}cQx8+`lke5JY3T58wpp}q2XAfJ)s_0z9KeU%`PhaK;M48p}?o17M"
    "7bw`1%h_eo$WKzcd`PGT>@lsm-lisTdgMs*i^e9HJI(8pgym!vPVgEfx${7G+yru}xR@WefoibN#MU4h9TOT6*5p(Wij@<+OxUUg"
    "o#C)|zj)(=mMyv}e}Y9`A}x1BXZHET2>#!8SZACijUj_`k7NFHlMvv(NNjj(LWY@GfuMEoz)#<8gh3p}A@79wZa%^}gh|YZ(CgWz"
    "@6AX)KTx)}k>wn9UoaQ-yw|Y4vsD;V3`dPShg*$xDzMc??#-09L!7c#i|o>YQ?89<J88Jw1r`+Qj;}e(w1)$v94LpJ<eCFrE5}K>"
    "Nb|~2@5B|1$%Q~Cz2QlnI?#EUiHAz_SwkJ9Wq|ScKAkdCUaWQNV>1>i@+Q;FEW%Dl6P&RC1V5ycfcmF}3lnjXutLRf*yX5N===w9"
    "h4E(mS*qVp9g%20knCK3+j$hNM|oRYSM3#;3oJ+E8-%CQed_fBi#l7Xmj@V|_pCs=CDw4^8Y(;+LO$**MWTxJgr1yR`_tQ9{*$=E"
    "m;rjb$xBz>sG}fW^eB+{J4h{zrgf<5KNKOb^LJp%|K=O?I)8Ck{Pde>56x#3?9fhsEwsO8O6`?(6@YwhC;ZxPNd_LfuC~jA`whL@"
    "DJZ1h(26h_pnfY^nSH4eHv6sdSf@WYEX?6aJ`0^6?f;O{8{rW1{M$ReF)aGarl@DLM|;h0SNwne9Q}!7A?uIcoDMr_UHuh$!~S(f"
    "-Ckz+d027q4{&!Tv`;jP_^Lb4GG`aPI7R$C<5{@qe8q2X!#)UN1*ZcR&Qp<4mXZb_?!)K}sXQ!f?Pv1-y05Ldvx;5qppQ5JSdhyr"
    "@?=VKM7`;!iE()!QN~!HFaJ1P{;tUTm@SyR*5=xWa`PnCw+&{QcoHV~nE#Y>Etdh6>X-TWSSpZ=NzCS2LNN#)fo-oI3~Z9hnPg-;"
    "(L<!tsSH~vqdE-_UDdXpQH<4Z=)5@~87*DN%=A9^E?$ct1uAF_whr*;1kF^gLOs{bSz!B2o!Sl|bwdx@2!W?&&!bdr1*KfXi61`j"
    "G%fKac@3((HLSldQb<=n_%43dd%9at+TG&}lT_7UmfKb?()kQ|L8xKTP?I5@v28RcsRAf?#Rr;8d5k5bi!jzr9bXyG_dAk33O#C7"
    "LXW~>Z5XDaSn2@`Lop#UU+euPBs}|hvfhs+?<1xUG?9IHKT}37xuf4v<<}YkeoK8&Uodaf7kZr+7#34E>+A&YH4rcBk2(|EJ*ji{"
    "q(N@sBN_OPpmE16LBmX+PF<u+KB2#(<MJPM?g(54rnpqv+?Ubui?h5_U%WNODI}c2BCba8a7dN}QlVBqey|(Y61}57l#^N_jjoNQ"
    "z!p|mQm#|yg)B+2F4dXV8zW^CvL@C>d>3XXeW?fc+7aX*W08?v6N$H8dOBd5@y}Sxl2xrIkT|hZbWrgnaU`LHQ#!`=GY&{5XgkL~"
    "?puzDS!PVM>9luGJ{o?aZp1gTI^tKBZjI42WKSkYOfj{t+CfM^{oNB$$G%92gnwW7gZbiP#ZK9L_J5s{4|N+(S*=>juY%0FsP+$4"
    "IxG#Wi!gAU&$n==GwOZ<bo41@c@A?f5?rj;a4wo|YZ|PUa%f~n0?`nM;Vs_FPe+%9v3RhLB&DK)MW`c~^Qp5bTe<tXY=wm`&n=$K"
    "{UMF%Vj4lXez0IL1`EdQR%Ou%TRdk_M;_Dn#C3K<&u$O3s^n#0wA8g|k5IPba!5keOSd8elv<Y{Z|@xi8g51yy)&7Nm~!!!-r7*h"
    "GVQ3%8&8Q_I|n-0wu6Lsp?1V@vz|_BRt$_S4fh6zom-YWNQzFg5L~*GP+EOXK3On~F@YLFMsicT(Ozih%;glCM24PwmexY^P%Wn2"
    "?oA6ittKcK7pM5_5xb*D4@U$;gSK~$Xc&gwYb3hE`+n3~c5p0yDA%u0c-ryQ^OQ63J>m=BgI-N#b|-ui-6~K#hN#{NvJP}Q-B&S3"
    "=GrS-(se>{L(f~jl@SUAfV-xZ!sht%Wm^VO2M%hfG84O*5v}WNx9=J6^cY6<&Cr{1psy0_=H80Lv^!c-ddwPf(<nNLab+8f`=6L>"
    "-P48H#2lZso&qdfWBAR24CQrz1Vo5opA%irY3d^4Ko24M|9<HTdvv?m>(Qkh_3!_oJHDVly1L9A8pk3)a_uAN6Qd^#Wh{iiauNio"
    "ZbQMJ?Z)yzwwthT-5{g!=!C*dBbX$wsI`25pn)ho+~Im4Kg*Due&_Ul1u^0bl87?@lyQSyC~uN4>J0D>3PN@1x_ny~@U1V(InCx^"
    "v7Mjx(8=i$`2Yp6@1P)g@e3%(_lRmLpu)NfdH>Cr?jr`_u_fpjc8Nm=S2?tlqJfzi%@``?pwd|5HK>ISJ_{vVnPJ1doLT#aI_sii"
    "C5xB1^Oz_hk@TG&$XY9JtR;N`{55rU!$_6CShezD%I}(8ZmyNL*Bx3a*#;`7)T4@bJ$S#SmlGEHy+;)~KLJBV=(V2e51(B=o4ez-"
    "QxzW0?qqQTafw|RF<{(jg1Hy;BKLDQwxd_Gs7~ECGDg2y5rg=7cdq@K;yRuO)*)G$X|KIcBnmOAOuMuWNKZGX_N~KD@b=UGxyH=c"
    "@geT%(U?n+qR74POc`d+FbVA$VUDXd?R86o`0VbBm+Mhg25BV_M;+j+;#+s<+9<2<gi=ganQbJUL-&R>r53EUKY>PuwU@coRLIFs"
    "FO1$dTae>qw4CsdvhJFdlWMqrbO!P(Pwel1n%E=J_-^v}_ZAsk65~smLA8JOv10iA(IQHlT*ED=l5%J#>5(weh87B~?s<@Ku1A^f"
    "^BMw-%UugP4;IygCW$6*#M^+Qq4q3ORRUN>r&3r&C;JeDg@ZeZ#!#QN&=YkBspB>Q<5ss_cs>^1?a<nefrMSGk*7>Xf>cINp}jB;"
    "-)S;vePPD$auoE}l%Ii;@w5FXiDkvJH*>#`N}R!&LB6XCO2%jE0JT8rD?_i&pBXi6A3o&BlxSJ=8^hN6L!$BTX5YrT@!W)Z56!Oz"
    "T8kph7RJ*rNQ47CzZ^vKirQ-ua7VW>8@j`lgK7H#L#nNfdoy?)ee!60G|X2^{MImQ^I*dnL8{0S)_uU1M>)tN3dUT59j57~75Xe{"
    "UUJyduq8yO@ZwOUp1Of0$!Ik~ENoNhOl?tCQ0qL)%mokb1B^L~R}oOYOZn*yAAT4$L?cvz&+tv@7EiS}Otc;~C{ne0iU(|BGjaNa"
    "Uk5~jr(OD(iG5?8$gGt`Celn~T#PiF&!S;zyC|QBTpJ`e<$hl~oaZ1Bz07~EF_YkRfy(VyNY1SYk?Un0G*M5Yp=s1x_J3o={QGfX"
    "LZSY0I{&)`4wo|)xX<bQSBt2Ll;RBpfY~#F?Tx*1@$@N?x^0%5-{*w_KY>#EHjuChoSm^(il}4H%U%C4$+_}_T^xXJ0?8t~2R18*"
    "CF{Yr-p|{zoq_@fRA<6*bWn<koZ=1EVB(n=#NnEKm!<Cdum1#e8?ya&`1P};|IF^6#7J!ST)n=QiJ=mI#tAk-Rj@|Cgj3~Ls`!;+"
    "-HufmyKyZ+iQnF&Xk~^3@%fy5h5AmkVQQo~%m<d{OS!!NR7g+}p%ev5AjcQ`=@|>8_WZHqw)q~8G}Ma>@-8Iw`BF`yM!=Ye0ukvy"
    "h&Id#I#4#3XkXhwZR{RatT0pBW8AeeMs;2~G+=QwyZ89W!^M-yYI77XHrt$|e*|&YxZA6T)*Tod^Jjb(0wD9;`bu1|0F{o-IY-OR"
    "a`Q>FVN?gn9Vs=Qj(1gT85mh=E`9`PsuR{-PXVjWA(P+R0kiAHVW#b$g3#bGMu*SqdbrNXDu1sn_U}X+=D0p+qbF(ELczVW<*7(|"
    "kOpc-k<ia^0wk6&w)S^e5iq_79n6iIXu$B3xbA?6sq>)Fr1A2dr?s>1Q6+*erg}`G!BD#rMASRchA}X4NZuYs(V#t>x#+uScB=?I"
    "N>#UUm>W11+S9MKQ>{WLh{{!c1j$bp$5!72Z;5YwNf>Q_CR@qIfmA=(AzU9vRgeg=p#a&%I0BgaH7<>6P6o=`2VrTLDMGu2MSnU4"
    "*~1bEz<i7@*W(w6ZLRuK;*O_eW&D3Yx@d!P{4f8Rpsx4NoQ$Fo9fU1Z*_;lmuxd^4)HN1#w_`!;g(bYG+y+*_I(JnKZbR`sy?%uC"
    "BFs7BCUJPkaasTte6nEIv(U9Rs{cfyA%gTb){9PQvX`xZ$8I~$SvIMA<JJ;?!FrjD4W)H>5>BHt41Y?`nMx1CT`M-@94{<9#L8y`"
    "i(R8Ge_i`6W%3I~eV=?A{{Th!M*zaFCaM<zj3b7vKVSqO05IX5UW1Q)BEV=;fb7wq^crS83<#KsWWu<ITn+;{Z;e^jKW<n)P+**a"
    "0%M5{P=Oev+XZqyQxFdmZ~hOy4Fd`W;^BxjOZj{Wn6VZV;!8D}sfYP*P%x9g94t=(UnpP8Q^$kiJ1O4cnvbNf!`_0pNhiY6ChCCl"
    "YTyKH!86juL~2qdab0x!`J1qD2Msk?Rje0n&`D5#>vM81m1_A<@(n-&{u6}Qdw2XG#F!t17-J&D*f)e2_a{P(|8Jf7SvLn-{6GKV"
    "ep}kYCgTDRN^(utgZ<>bz+yW4GHFF?_Su@uw1!XW2G1cMD9@Xo`>mRIQF4%#o}9W(uL;}OzpPx`^)`kcx%1^lhQoGpD*3~*LfnHc"
    "?YJ-MSb*Muu#}Aa`?E#&MSqpU@&5gTf;uW|73~})Q8X>Ix*D092x}JP?ENHoLywv0NW)M`LqhB3+XSK~@4Va{-#Wpo5I?zM>B!Ko"
    "sU-Kbj-I${mpa**OR|PKcsCxCd$R>?8M@8YWe1(33Vb%%xD7+L=63e;<e$_FJ@(Gm3Os$Li2chKi_JEX1<}|=X-p-XmMIVM`HNNd"
    "6g>J|^gL?8{2`P8nR~5Qs7>dLUP<(T(!?(oZR62hv;$46pp1JclV6l}7RWzERDJd!GBw5JrHWasSEDS`tm2GJ8=De?H73%8(3y{&"
    "Ova%{yLJ58byR5;cE&Bn*v)qQJvK5Ir-nz}Io~mj^!5^ti`xR3bFE9|j-cteMbm3f)7qLqd0};QZ>*K`(vvgL9zp96PmLm45QniN"
    "+BauV9wu&pik8#8%CqCsdQ$KmRK^nZ!+%+Gd^JY?nXoc5924P);=3CM$mdupY2DGOskPCm-8!LJ$1O}&BX`Gj8sDtxU4O=1=JgcU"
    "6;dD{eE@u$)5Mm&Kkp_CIyO0`KuF~kR|4<uWe{(s+Ssdar2iv7(W$cxy3>8U;8p|L)e$XQO@Nt?G^P>!pDJTo8fv^QMrXFu!`}5q"
    "hWmw=meb+8rY1CQTn|Mo3I4pA0H(+0-=gq*vnll;6}asT1%$P}GK0`wS6>84@8mtc=jzYGx`%1+1vL5Zp9rkR>N?5<urk;KieUbb"
    "VlaLC1$<Vtt`gzXsU|>}6h6Rb`ZoVxM>XmW83*A1=Z$O5oRI^pUX4MvQVq4QiBJ|~-NhVQMTuwwAle=C3F{&DY=i+fOXc!F$buw&"
    "&7t{z%Yruu+8Y%w0F7I`w|B<S9O7~o)n0K%wvN_<gA{bepgiEwhPw#K>~u7e(5B=;BhotMTWPK#`fewF2)SuD3u!)(K!v&5YMp2W"
    "wy_(BHt>d3>S>iu;fDg{jm#VSld1Zg#EttuPMLAubmbWRdKs}3rj+6=?as53AiFZ|2^0sGAtCLv=PdIUl>-}mV4}`YrtEtl`KkjP"
    "va1OTTh|30AFuVow9-K`U%Q3&!+qa`qls^%Q_NL>U20X4Kr(r{r5d%Uu?%I?cM_(ANrPbC^b1g9B+LmbS$L0O{7DQV9ns$oa*3$q"
    "i-Ue%iACC(C}+aaJ~|D6PRO5s5<ExN)3DEmI0j?G@<<G-*kP@7DBmty)N@L)7E=5BOeG0=Ahy5B`ncD@Lo{_F-fj3PCsJ6)1(Cup"
    "@|CwvGp5QW*-)(osIPeMsjBtnO?Nz<u{us<J=~;xFgz;eR$cMZ61<_oJt1AK?v7vBWj$4)>DsXe-h`%o)ROYtB4T)tso)ZOf2*Jt"
    "r`AqXd%-FQUqU+4;Dh6Y`?d^l%Ep#r)6%^$%xU}*GV9<FiqvpP3`GqoQoVKRY{-sT-K@Rx<#GQZaCv*NNrP<cw?uItP-C?lX)*H{"
    "LOo%=4MGI%-Fudx4(glN0k<>4_HBX&WG_~pin=R5NZpr&0{n;Q<-NvC!msrz)DpEm-z%xMOT%kZI>S8V)D(oW;D&p8<I^@%zUBe6"
    "ING2FXj}oX@aiaV)VdzN6^lWT*w~@GwCqCZH7)lKwN4hW!Dgvf$@vW8WAW?7bO+qf35!AfHJc6kr+hWosS9gGd(>J>m@l4|c!$bj"
    "HME_LCz=WFwsg%?oaW9&1_K+bJyXOyNYOBJ4~=Ke`8Ml)xKA~}*3#`rJ(yB|h+{azQv!+Mi*on6`UxLGSifN^phoVucPJZgK-rRv"
    "7SaEG{plGAItX&tJ;lZL(fbR^X6_3wC>uDZd)N>&DqM@g)U`@DY@xZ5Js~NtP=~qt$OskF^`=F~CBYG>7b{b@^1_vME5ydhmsD=>"
    "!n9GOMwmPAoeFL*HwXH3i?$o9-+21|qVNm(_V(!uFQ*!Kzi9Ph4e{Bwu7ytJs?&QQHf-wNb=B}%Y+!qA+-*%hL-FeHk__?H8KzG2"
    "Eeq4bKJX5K6O7##x31`%mja_59oP-dj|YtIW*g#7O{ks6?kSFx!7QcjcvZ85TyxU>guu1+0HVNGXisA9^$P;`lIlzd++giSGye3b"
    "J~7;l;v)yTko3*YXcIjgGFQdz?-S1h*&kg9fm`IfUAuXAJD>7wLnUS*%r2q3YrTO~D8|v<q<D@h_C{59%=Q_@I^0kR&#;|i*+x2K"
    "otEOXCDl2p?)%AE@GQj11MnWPq_aXATL>jZc4do8a9e|d0a&!T`QG8Ne8sDens5R32N6dF(K?>iS9x|)ywSZT&!vf$A>{H}bgQ3z"
    "4HUcXl*Cb$Wv*O_m$T|{GK4u>>F(}$7kxU&TEn_B*5_--BMvvOfE_=9_hvASO}vx`W>O|1j+}gq<=8156T|L<cLbf18g3@7KKF*C"
    "FxIrHUlWGvl9WSBMQTp2@#mR%(#xSur}nz$BISDJE$c8LaYmiZ^|)R3mov0B4DE8FHm2uvW#Xk;2EhPYhR`}|(`gnfnl)v_4dL%Y"
    "OR=A0aYoLrM`t7`WtStE@O5q>9BgY`_wN^ZcC>h5;&f(vy|wX&wZqnXB1nwYyPLnVf!W9=qSpe<ncd+~>Z6QOvpYXmhN_Xlq7Qjk"
    "pSM3U=KS8c!<t#4N9`2+j(&u%<Hh%dk9(6L%tlPQV8Xrc8Xtll3koH>&fZ}Z*>b`^713pg<o`c!AQgPW$59{SmMUev)O{yf1k3u~"
    "<%$;%yDnZgbf)G$n^QS!(bZT#JxQPJMVNfZVO`&vvI&6B3`2VoQ57aN_SwDO+DFDVwKiYfnYgE%FRYy2pQ2t-@`-3^IeGg1Az_z+"
    "$z*6ws$!vMM~7a$-1bm4s*I+`zbgEC^4i4Bapc8}@nXdT6A`AlgKDDu=g+W-o8z#4g9zV*T32u8PLsSze~I4U|CBL>aWFe*T5iLJ"
    "JN}AfqUVfhYz}XHU(~@ThIxka?{2k4NgJHS6v~Knp-g)o<bhpoU^)JbgPYaWDv}IutstEVx(?rw>ozS~#rTBEZVJ;+Zl}M4JMt};"
    ")O?51y#}8?Z0O-Xj;y~e@;1B+CWpIuR>lY+M)xI=RU48x_v<I1SDhqGjVz~tQd|h=z^s;Tm;ALH^dGDXZ{{j(ozm7ZfSLC3v<gi+"
    "ZL~qcEzBp~8*<yUAAhDti((~(Z_60+KzOd9+YICdx~=&_)qRY^qreiDT{N@?b4x9-mB`T2_R77hTFZqtlw$i4<+4X8{1s;?R8MI<"
    "4tdVzdIU&e^Z|58+r#J-@AG>vJ?@<JcMDqgp^wAjFKUDCIh0P?XCy{T`B~4oS)~)|Rn?|LficFp2Z>;+%5($W2swRZi?QmmTI5PZ"
    "yc|J!-A1CrYKajb(JN%Z*z$IpKTr`Be|qvzI&&Njl?He8rI8iJ9GYOeKev+V;Lszz9QUN=0lmLd8SB(YRopW@cN*;Y^*fFM|Kqjd"
    "fZtLtwB4)vh7w(`|2%V;#xHO6FLH<Qt0HA)xAcTx^`C##zY#PDv~m3zXZ5DbS?IPJs((Ei398nh(y=yKtp7R(L%!8Y2cD8e&a-G8"
    "e#Dn(gieL@udV#FjreMt2p93^^?`16m#EBPvx?yf?nH-4TbN7;#mcjJT=910(3vDqVF#WIPMbbc?v~Z0>zJ&0Qurq98V<dc*iCq-"
    "yKYp!#d6=}&^u}Ybb#cW;%Hg&@H_5Q3qz)U)y2KY&>ugw#e?GvqNgyXw}>iOifZ?lE46_}MU>$CYg$=#KCHH+SCM0W8iLG;8}_uv"
    "ZlPDX_W9x;P#$5uvZ-9kFr4Ry>FN)h$#esy>lkVJFn~?}w(tv-_s7<NgPYVmhxtfnI^#3F1#0V-ggU*xAkBw^O;p|sFNQ;-uwac}"
    "rc6migJb1_g^7Gxr``4`h*lmgO@>b6&5du7?tV+{N$l7j%w(MtjZ!*!*5&S&kbq{930|)2V-qeC^42C>yg4G$rSB0-l!PotvYzHN"
    ";<O+kFw!r2ls}|HKm|;(@rBT1^{*gjobgm*S-^A(=nUK2Lzw9Y6W9=r2E4jTfPC~x(K*@2f;2DJBaUgl2U-7Jf^jH}oX6hufF?_w"
    "#)2IuYTlL~3IP_)>7$fH=l1@f+z@%udJqKk0agiyC3JkWRL5hEn4<37Hg?mEd~zS_jM)ANZD4&1j>D7#KVZF&hAX%iEwnAsJHK|n"
    "FjJWKW%I#M{@MZH?wnnCckfDkd=nBl)D`D6XwW*DrZJFT#5J4Nx=(EAfZYtQTfI$&7dfVYntEb!4MVq8(=lIPF(>T+`Z^!TJ#$5+"
    "(vMsS?SXIw<>+-A%Lct&z($x6K8(zoqqM3x(kGpT6`U8mg;Jc!6B(a{(7YRZzD}TMbGZdvCaJ=074jD-Bg~DIYFB^OjH$KVs)8>N"
    "pD~b48&n*e{cT?qfZ{0$6Gb^l9tm^VWdM^KMPT77Pcd+@hz9ontLleG)G{^VHv^C~$TszJwY)D-<gGf{1%9%-V}kfhH+70cAF%ol"
    "TwmOr2}_9_(@qnz5ctdI>I8?yocx;%`5>lVz`l1?q+6-8reYCEia6NXf@mB;x-rg~s>p1+7q=C7T}KHRPYh!j2Sj-Z3JK1H_wgoT"
    "kT&!#u9!NRz)X*xRw};X1c!2%;AcMnWkvv7f~GH!pSiTK<j5xF&9e$+hlS7{Ln5dWOzaA>X0ckFz3Kc}2kx^g{(<@9bV>z7WxP?}"
    "L4S;{+~w&q@q5c^7q`R2{fR_%q1zkrX3*Oy3R#Y+SjyoD8KTNKw*}*j<isDIEpY+23}$@?Q>h5UyfhHy1#mxY@@d$~<lk|BjA2&~"
    "hO!~Tx(0qv<(Het{XUd~p<?}zTRj@7U?`^~Ku+!`D8&Uq+U)}G*KoPqsgyzYZVn0?w^U8spFk?413oC*qpF-+b;ddAX72IkFso>f"
    ")jSVk^FvH`u(hsqH77@k#5&JqZuZ!Z2f6$^?(Zj(r5;FXk~87kXf-#n-Z`Sei%lwOw^Qf$Ju2w$#<<$85zY82p)s43;uc6(r*6d>"
    "eWXxfZVctcB9Y>Ha*hh|e1a5CKZ9~rX%w7i^kfqRsCSdDAfke$QJ13PXuj_}i<z$l536;ybLiDCaU`&crI(dWoTI*q1dOF%7g#Q;"
    "qh9u?OosV+Z{xXcJvv@;^5#TOs!2H-JWOXJPMGnX#~3=|CnpxXcRR61cR)8#kWKP$f4-vud9xLn8#i?B-J(4MCX_t$?JB5YDua;*"
    "6~T@h#tjRjdI-BoL$pZAJ-`jrEh#+q%CiHcOMt)K;kgIpWklCyW)=HL0r7NRjZOI#4prk7gUh-#NfqUHXyCsdlY?o*N{JUV){47Y"
    "o|=`=_`CTyhb0&!<=AAr=KuTDJ4}!<&~PYMS?Yd1#lX;Q{LDJtwLm%@Hgi8<g3J$0FmJ&wQ0|wDA8`?Pe`V;^_$4FcPipprds+_n"
    "%MoY%2PXKRGz?13T1?-AQjsytMuO;CF`swN=b8;OVps@ZFc>OS7tn`J*r;6C(tD-~61lgkO1acKOz^8=zFOk9hFR+Z3D##)7)tVA"
    "VI=IRUEr815%GMTgr!w|xLT*qKHp_7iYS*B>WdOcf;<)Rgr!+IP*od&0R9>HkAA+x1&vkne{ZC0zvua5Fzr_Dtvr%Z;CkYU`UY0*"
    "24w9h-H@oYN<&y+crTJ$?y(XVOw)i#M{C(#a#kjVZEAVAU(Huf&w{GKcl;p#>gxZEmG|!l%sYPYX8~|a<DUg!GL9V4oUV+=8oX+j"
    "UlsrjaMi`;y|A$Wgns;M(1xB0|HT6R4kqMvQfl=5yS<X}xbEKe<QPL$bcp73u^Ch7`{#?PO?cZi<IKVCT_`zAs+Buu#F#Ih$Y+>_"
    "H&?h=6iRaV9#BrGShv28%<0R-k&5IiaU`v_P85IG=OS#c;{Qe$;*(Xj?7#~t9VI>_dXS;~)Ed@ZN<MQzHhsg}Hsy!Oc|-#2xr$X@"
    "KPbc3ctxkIwqLB|85c@5yk@H8{z~;~$CN*H+e~;@Y;|m-laXVP35U-UB-_oc?<hlKyl&jBoE;xGrh>3<x!7d7;X+%@cm(;C79>Jk"
    "%Q|$GU``Akkpz3D?>Fgi)jwL^!@Lm<*{|Hddr&u8XUZZIz1<S}d(N@9_c7S_5YLFARhjmzx~z2P)<is9uAd1_j`a?6>;=_#a<(Ql"
    "yHy?|AWn-bZCLLwJ>0OcM}uUTg;Y-AiSd{OCJsxN!kSoz-eHGE{m@qGNPw(xOdx52K3RvkVUmjr*St-3NCh3<g?+0}p@H28sEym!"
    "y-_~YN4!8CuT6(FidM;EptK(yU^=*X#~+&WV%O~U+}Lq)#Y;-q&N-anz&ULTkD(w_PvTWmU&z}En)mfC+Th$?d+y2-{rd)Q_xcGy"
    "Jmj<|K48<tL^rR4Jr3WL%lG&?jugaqMDGyp_TY!7?oDVS;cT(m%Y%;@HJIlI7D4kwx^fIAMg-YLd6%~Qv@c*~`qqoik4!)p_9L-("
    "Fd|{JBC1J{MW?vM{e-nmH#DgO6*LmM7-&P4^~m4Uv)jSEh#Goxir6b;d+xHwwhpQVQ&K90-g3|0Z`pbQ#Dv;XXMJ;Qi)0(5*PiO7"
    "Z-Np{@EP7St7<V@*B+5j#pj8;)PMY$dB-W5HE2kRKTFV?Z2LLq^n;aPv6C81pcJaH=<^DEu(%V^=qLvB#Dq{jkK`KmP92em&BU&*"
    "YZ#;%Sr9<VTDI>aAX@W3u2L*Ec;OW(0@O3l1m@qf;fZ^_V#d-e9(R3H);~T<?Hg4IX5?b~1HSlf`v)Mp_ExV7W@7A?0*4@uipI-4"
    "4wmE6$I0{HJrZ67tQ>U^?+^XjFDWxjN=*5LFa9IIg}a)tmW_Sz1916|3jY<P@g1D<2c*$Nx4=v^RU)x&K9P-#j%;Lp3cjFf#rbgR"
    "{P_vl{vTLJ)_~b0ndLTpPWrEVdi5M0%HHPW55VJ3S&hKthah*IS-9BFyZ;05$Qxu|eADshYv%%ur@3l|42=<2D;4#l<Jqs!ALvI@"
    "@$icGR#|zU8Rjn3A4^efFn4Yy3OCZmZs8Qb6KWpO>zB6Y8-R{=vKZkh{A4)N&d7iOa^0N=)UCzFqX0)1?aEpz*ZF(r@`;3`2oh4n"
    "P5YPT<R4fh`+o<EWDLSyIuz(OzW#yz)6N3<a;}5iWO+3GagE#$a3rIHBafTVEZ9|+g8NVw$4-!;FN)F$`t2`pB>hFCgPBEc1-EAR"
    "I<W1Q3I}u7_?CELqRr*30?FrFVu+N>97+VlOEt8|`nV%>HpFHRqV#S{qL}{-Ibx=T%*eG`FA@OFO}5fzvuWmLM9B##t6FF+E#I(`"
    "L_19DLt2Ltcb>Ok<tIh^sFhba78ct4xxLqiP!e`-Yb<jlxi-}od7K`(BwZML`bWGhCjpHHOIX^7R`Qg7V$1QDlCNeRIQ!g6dbCeU"
    "_ee3e-`@5DQ0o4dltHc>YmaVwR-A}*O1Ug?l%V4@vF_b5?2$x;%8wQ?EA3{WZQhFyShO{;^+AfKdpi*Fx|W8_;F{eu>2!A|%Z;vr"
    "1eEo{zw4ish%$BiQ(3iQXv(t5(9$`q26iy&OQ0hnBR-P-*8BjtXp^k!>7Yd|))r;^_NK=_O!de(pKuYOnY6vol|LbK^uA}u-l{tp"
    "Gq5;}rw~*-KAM;f(0q}tk+@QSn3l^+$WXEoy~B}jq2(=JXZ)UA3v4f&$acgn@7ZE>GZYW&M2_;Ol1XdXF-dVT$0!QuY%Ks~N*;lv"
    "b5xXEgUk?SuO%-4`Ln9{+L4;mElZp4Xntf&Yda_T_YS<IO$#Eu%0Bu2V8<@X@Zy3X;=92du<Z8qX3#}z)D@#FBgLhfYaO9fdpukH"
    "xZ4BhT3Jd=TjLUp<-14UwIF5QahT@gcbqC_0h_QDxKYP5gThv-57)V#2l(O^8=Fjok2pRNL?`;mIKODnT@b&vJ!ESd6v5dQ_R^~`"
    "K{ma^GGDZ=fOh28Z5OowE~Qj;4|YZGDR+zv)Uvw=3$E2B8*GlOuEECf(2Gpdbq18u+TsnLY51Oj7iGJ0km#@(b@3Gb*@}$}tS2><"
    "Ew-t(BN#sk)zq(dd_3xpIDvSrPlgwL{a^ZK5kN8HW}=Ey-)X&{I~vyM-!!;q{I6iIAK?Pg)L(_B9tq}dgML7MM{P2?P)$%G7u|JR"
    "9t>85bPHqT`GJxSpr3qzEc9tD=6%+H=pGYnDkPky)W+MwOIp>AI!tgbb{A=dk=twV4&{7{VL@gK9jJ6Ks}0exGnzs@{8~w1vQ)m<"
    "Pm%84*R;|Ma!Q+1`&99Sb#$1<G=10Le8Uje6m+^j29o_Uw<kLoT9gViC<du1nkd%-=Gw4CujLgR&qV2Axto2&E?LX$VuCzhj@9^!"
    "7;0X*5x8OFN^dS^)Ut~3KTeq*61qK;{(f=%4vIIw_tIldOgVVJb$VIdHjHHOfUbJQ#25raB|7|-E8e(bF(}u4G>I^$^@~VYmS($c"
    "OYkZgw9xt;@8Mz$cQEEX0ukv0dUqW4D$h99^zZgQVL&Z=_xWaM1QA?Ei5kCnR1>){!LOqAziMzI*SEz+&*ulkaT>|}+t@`npYc>V"
    "%&}QlQCMdVk~C_{(@;9Os!5KM2@w4r3K&bLO#0A(msY(a!)#9<{kEXvNoL6)GAP_tlEDrhlRJ<T)iGLS8zLGW&pyd8$w%VAM2pf("
    "<5A=@$sNY}t7n+d(T^T6XRs(ttqr+kSWtdaZGR^?2Ewp2nN^cWlwZ&EMLgyhGp0Ij1kG!s=S4XVET~+omfSa@iZ{65Qzne`vqu0p"
    "hP;oHdqn4R4Zjv0oo%Di_(3CamLo1wR9ISVweE2d*rArLX0p}k@zEMF-GxmRs%4mE%Tt)#dt+#Fu$!Bp23L6fXaEjcm)UA-*(<eD"
    "&E1`C-($JF&%~5|d<Ev!Ns(4WEvums$YePfYXGcAp{r1?=7^&JI%}$u9^!86Xx{af<?N1vVRwp8<VL}Ln4|A5gS|n{iMKt>AdVju"
    "hdD8F0zUxL&$ggW*-5vNACJh{+2y*o`_Pw`Jutp-IQ<8@Ii8=(`A$Zg1d%u@WBAGb5hv7dw*A`5YgP|0LtnX)Im({a361A_24qIr"
    "G04gNt#5dmU59H~PPi@6`@T6Un`qOo9ziQww=Pq6GS%*ubOO4?!yMvp9c8p-vpken#{l*u7i0OvWeO-oPCKRhd3SHyBMQv;Mw^v?"
    "z6u6&`>bxpr`FS<3K9wbMf9RG20rvi!K^b~G2#pTpEs^<v;`rVzSsHr_p_ILWtccrJ^s593O3F@EA)En?`Tlkb)dYc3-4G+3_E*e"
    "Oa<Fa#9KTMfWM>}JrnqKOT>b1=DL_-KI5EfRjkoT5wI{FgoVQ*Os`d8+S~A|?twI17Z#)1=6)t|U{;G_DVaZV#SFnlGli>rzl+RZ"
    "PmjsN9A~xI3$XfnG5<3!@y?o-%RgH#_^ZFayyFF2eXrPX$d=94VVoJXT~cmiwP-cmnpP^?F?hX*cdVNueYxpoPBC6=_%tr72HIuy"
    "Id?pFywGl5+0eZ0a--g5bLG50T=Rf$IIFqd0D)IRVILJ)(c{sAnza~pXs-KhvWrUYPOyYm-dGM6t`Q{gGlLl9WcWnGvgz<^E$;kY"
    "Z+x61<SVb#3*^e0L3WI7ANbnZN-Mj1k1BCYZo6(JHA-uRM^zrlR?1V5@_Jb7`n+}<Ongf%yS1GX)!>?=-9VmiyR+-!bm^Ywsw)z2"
    "J}#gj4=y0PPlQU`umrP80H6o(vk*vBay@@cS}wZw<rW4Hkwp<mYAnWBE>!CpO*HU;*t*y0E_C2vfx3<*?s613c2@PCcic(BHqpk|"
    "7Kzm?OL)&EU!d1-N>fZZbr9!9i}2f|85S4yScO&&Fwbusge(r`=OFq2G4~$2sx!;h=(Dg1A{-=VjL5-Yz~s!8OwKt6H$3~_!8S10"
    "`qJL}9-XzMsp;8vyWOF>s(REYJ=WFd+$_~&PCMsZD?Y2*mlZ0ObMh!;MKpa66^br2pO`<s%{$h&dSEZ$slA1IYcK#Z9t{na)B_31"
    "gu@yc3Q_Y=G_a%<XTb%PwF*6oW?YGAQhX)Dfjpx@i6VG_GJS;L)_Zv2o8fDHDRMJ)T@SRDi&fEazq|LU<e%tf2fZtlT({vf(qn{H"
    "w2v|*zo1OCW~xR03nu%y^)_bqY^@WuwyJW;<;b-1OwZ$#sLX5AMQ%+*h#xMH6vY?-kzt=1V+(CKfWLYslS5>J>$thO`anMMV2zzt"
    "c02~tO>L}>+7q@8ERG)Nj65cO*5t4=dM2UX>XkU=-iM!fNval5s^JfV^FC4p?5PDX)PV_~T%uk;F&B_sb{_--QC#M8MnTIDq<}}p"
    "1%tw?AmIXj+qM_SQzZ(m+WCES=vTdG15Ep+4H(@YOBoeX)bD>I_xYQDb>Gh?h<=v(-+Zz0+ZXiqbM@rg*8Rc}^%M_jw{X2gIJy3;"
    "@{e|RKL_~+tLI!~R%Zgb|C}7W7tt4`6YxiCpsT_6*ik1E(2nAu$nS>H@#@MT$IFP!5PL2%!vQ-K?eD2-r_oEEE)Elv`(u*e_S2y~"
    "5Nopu9$A@*Y`cF_K>7$p6#d;N{-EF!t!tcG!kfE(plk}gh>sE<zrUP*L3ZEAxn!ENJ-mp?YsotQdj+<F?e!`QwOPlOcd9<h<h|4-"
    "jy|U3dAfdWca!mS6g{e0wc!Pj>OzfkC%Q;HkU;V=uK3m)eNV2Qr63?hpCMhivz`lG{8;1~9G?%D%Zny0n;lixso325$lFra*5i_y"
    "wQ9Jbl+=wJuO8XJ^!mT%`ahky|K1|Y8;8cG-v*ZN9?0SC3+2w^Bfh;TMm5B17DMx<E#AdL-~jTkTktjnHvv%HPQkY9E<Et^XafmP"
    "K3dI2R#SL+I7VC}d!1hOZF6)vpVz6~3tJxe(tnJP>+j3AUGn471OfjPj$3qKvrFSS359G#gxb1ehFiT<*FqE*c&_J|T`vGf03>BD"
    ";R0K+CrbGgRf^&FwM379M+yp#s*1NZ(h%|Z=otla-Fl3Jqlpgw>GpaA-M+2UK1s@xGsW(Q!g}RP!hOF9<uFvWBPe<$ty+C|m-tdO"
    "vZurCwIC>qhL2=if!4|}tpu*=kINr7|EP*$A9EjkQLKQnq9Kw_TgYvxCA^dIe0%u<4u5aD+b1pSn{MqUsLpYHjyByq)DB`^JWn~d"
    "V?*``iW`H;BE-b^6rDTp_-5Ei;^p*AZ7gI`f6q33fl}Xq;&+cRpFKAAgqx?&9!t6`R8Fdgjn7<I#mg?h8J!?A-#sRw%hdbQUr~7T"
    "<|fqSC+jep*%GWO9Hdy!Ikr6ToixbV^JsH+Le-F|4(^UbZ)vE#4S%pgH@FXoVRoDKm|$c2=Uxr9m{L_TL{fJSvg6L0^anEJW2%~5"
    "BUz<D&4{Vs0<l!+-0>4wnpmz%vx5piF6(k%s7mXcLQmuo(QQu`TP`bW+eyI%7Q<*wwG9;V*AUa<%X;rs!p<0CXu67x+a+34{QEm%"
    "MZ@f50iX<eZX8gBR6GtS4#iC|<xK`R2Gg_%nL`q`EyFT;-!4P*dpHg|I6^l^RNA|b_0G*8!>pGEB>7vfdZUtoKQ`}R=4Rb;Kw*Ps"
    "{ObQN1z%w0pIavPI%&@Z)yDm}C~ML1KQFjWnNt^0vtPAm`t;I{fvN9U4%gi2<{q$Ym+D=h-Q~|+rrze&-pr>jCW`q>%djwuKBke+"
    "_0BJwQ-{bS1&=<xHU$5u*gFAid8_^BX$<uPwn7Q}=A)ir9JgLWd!?zuc<G>a%LJyDphkfu2iNF|0Gg}X;WhGv!jC7C5DX%yh@Fh7"
    "o@C*iJj_4w&BP^26We*1>!Cd2f=FvGU#PsZR(i04l{1Q|5us9DKY`@k;zdNLKA;rWQ;K;$E6q`{-L~!G;pJG8v!R+o?-x{Z`5bV3"
    "#(uGC%Dw`W)Xa+9dmHbQ)nb6N$iq`1kc;(d*SPyOVhS8Ib&@z^6*O99ZyPQ|&4(DtH#jXUY)1A$<$cF~bi`kSC{MDt+nQZo%Yv$S"
    "KH<+_J+8>zD2iX@GeDW`g~hQDR#3jXV)^BW3UJdG_ub|rfX_)*z1kz=4N$7Zh0_)x1=DJnm)n3&ZUg_JG*2s#&-YQyZVIG#841W)"
    "P(?;W)L$vA62PC`ZFR~bUb^?%UIQ2nTjl-OjOon&q9B5~X+UdI6DWTl?dy~+t9twhmuUeZAM$|25w}vT1LbyZd9TxzgHWk9?Wr&V"
    "FW3zlQIa2tGCiu@e|~9zroR_C3Wqt9MQ-5mJaD>2$O(@Kt`ospQKSY%&GN9BGaF_%Ilw1`ppH5n`ogmoSKd-=`waVxjv&{W+<``0"
    "gRt=<7d(rDN{Ge(b@=`N{Wx2(hZ~mmU=egQaA@o7-WXCiBZ)m+f##?ZLN@7N7r^QpUvO&UjKEV^@#r|7nPLtoMFu5w3IL_Dwo6_q"
    "If~H?w17EtDTc|Avtdg?Nx|Q^RE>97qM2lhnxfr?*$@y!N?EQxG1iR!Hj+~ZVF6;h`RIj$Uz`8gWk|B2NxU~9*QRbo@D+3c<O>X8"
    "o~az=M<mouC=w-fYnkNEk$d`D_4xTz$|Y0D*m}1zfY-iXf!9aB0lfC<q_9xY7n+vA93e%@I74wE9&>%duMNBe%BiF6JlCQTW&U(|"
    "g!~Rmtv-|h&ttL9PFXZeR6^dI95euxS+zA>@xJ@DkOKU}JqN<;>4gg}%{GP)uY`^SY6c`*KN9w1h`ehUPBo2OJY3U=fmu#<*Du9P"
    "L5c%Q^>9=e*HB$8eU<v?gl_I3TAU}K>gg^*86oNdFa*+wr_hPa%r%U7yEw2cF%I~8m6sGeoO2OzbshwJvt#uh`^0MVMy@_ZyLW3n"
    "sfuE_rkUs27Kw+i9wM`=>TPy4*2Vs+C;o|17lRU1n`X|rJv3bMyuEwLm+J<48?RjBn++kh^6EY^6d0-}EvBgLh|4y4X3{-vFY{0b"
    "WfyJw+_R429_<?_=xsCr*|vWK7$I;xTyiD2T$jBAC99!Xd_8uKFt4(^qcLlnMso*Lv*mD3@%_^-p&CeTJxQq!k;%us-Pg^VgN>TF"
    "@3Dw8+Z|>_6)>LK!+I3MH4`h)Mqj?xeYf0o&>YG4Gy%`$YLAw@@LD#sUv$_aouhm5iRyln!cERAP0RL94XK+#E1zBhrAvAAY)&Zs"
    "o|JAkjkAsgj_O#EThK{oG`<*k{^S+|>ur7_ek*<Mz5-q<zjSwc+S0MQ+bmFVUv{zVbjX)}2+wWYjc`Xn&@R3QV4qjJXr~>*ZmceW"
    "e4(HK-9MISfUY|*co+vdK40ym&Vw^QeP!HTyOw&)=-1M7s-^4(?)!~}_?q~C@Y}5%C{=3!&iVOREQiJsIHBhrl&pRTODlaU-474Q"
    "6L6~b|NJ)t0?r$RsH6pQhy<CVrKewxBhB5_M&~~+`vwf0H`!vbz#^;k)qDr4>udO{fHdL{3kvym8P23Zz4lPb=~*lJ2?qZsQX<)^"
    "mqWQDN28l9fg{_FqMOg2d+hAQHzN*|F}XQkFM7(Ck@JZ@6N+6mX2Uhpv*<v`RPtMC*Jqk-pjb>U+23^CZ~E$YUAHEh9ZeiAaKX8)"
    "64wl;o<-r&Ot?$X;I2(`J*{3<U3aMh*kP;kxMy2F1nJ|o@?H%?J#VFk!iuF&mBX%%+nU_<(IH<GGmVa8w{aN5gy*kgXb=3yDLOiP"
    "?J*WYD<33)dmL7<ZBpe|sBa+1O`<;$f7E|{&TW4YHH}WMS1qR=_+-GYrjm0_n0sZw-}5Xq{TEP-FTGm?Dmf!jbHZdxJz<?}Ry3=U"
    "26FW!1Nl{)_0GrJjrJc4A(hUjTn4aQ{~~kVSXzO7khxIE8(lrPh0{r0zm|?bl}DRdyGu3<@u^MW&5J3;$6Bj$X>|<iyUQrw1N`oF"
    "0Mcu)0x4cNsG778{&Gf|i1R-aL%M)&E_?V;(!ORh0bLBaUDHo7^cZNm=x<clKn|yLF;r6%kDcZ!jsAL5G0^8EnXRA?xuqY7&R-Vb"
    "6Gufj+KBT6egzIz*T2#Ds2`V~AarB*^w|?sq`hv_zUFwf<P=Y&kyY*EBlhI`xZWWSa?%Z2P}j&E>v>qiNJz~^G|_KWn!YnaZglp%"
    "yGzGf9s`bUAZ)O|2TrZ3kqXaM#R0>3cd7?2Ta|qK&s$I!J?RR*W+%5KqN_YQz|ITR%}55+#=xk5t_TvEnPGZO_}jT{{07(1Z+{zQ"
    "`vI+1?nAri;JGaLRR|7Qe-M|bWqj>_%<~3Z{X^Z_OnnwYU3Zt<YDh}3)eGR&{tm?2O)JQ=t=>ouAE*bvoHEe7i<XMkthyk^q#_LR"
    "hGMeh^o$7_AJu9rOUXp8vxF!YOP+?L0zZ|hCxR61j!Wfxn6Jq%E!ObxOV?04#~T44-e-=eLug(x1bx?e`8g2l-qx1a5SqfV_&vCd"
    "MIy{9be2)BLB0m^loofzDu*gou)Q_sJcEMa9pubCZ4<pk>$V9%{F=ELkoJ#0K=b@T37(0i{0dYY-kV*XA*cS!ZB3^Op2tA4Q2cVe"
    ")|$)vfn;$gth2~P6y`u?W<>^Dd<Nvu)&tVF!y4pWOgkxMY&HYk?*CYVd;U16;tX|{BF{RYuIRDD)mLADxU&=j`H_w8)Oj^_ol*&r"
    "qFrHMW3ubMNGw^N6%Mo-Jqid^ciFi6eW-Bw#$zMQoL+!juz@`RY5VFG@{q}=tei9I2hd%gV`ipDyn@-gwLl|vlD<JBY+uG%LqK78"
    "4O4vZxWaU72;Kj}xO%8S6*g=p&BqMjNo-_5-+uxxY1ZAz4Uq|$dx2PKgR=L<8-ST1+>BwZkfh3VEVH2KS~?mXGZlc0*$2wh8pnTA"
    "2fhcb-<K^ezn(?)?d6;Pj`seD<8kqOKSA*fL0&=wR@BOXFTG9`J{Udzt;>P|jQ{#R*v4auPy|!atxfGS6aoyjo!ZlWE+A60yAH^q"
    "dq+TFC7Ig!K)lgHei=HaX%!0T_?Ni;xA%STXPJRZuMfRLyhXzA_nMG-h6IFB7(@5*ud?@qXYJRVjiiGtV(Xmi`K?2<3Ku8@K)33*"
    "?UA>X{&e4(DEgl`9Xjcp$dM3A|Ju_uWnVANQ|H9A@7witYb0YOupp{bv^flEizcHmu;|j!(a>G~P-4#CnUzAT=hi~8Jp<gI@PEVW"
    "{}w*+&%qM^=!xGV?SBI*G|~1xj7{_*Y@!}WvZ~DtNaQ!*o+E&J?&Dq)Vb4mz*~jI(DPQ!$1V-<_w|lYtHk4SDy8*D=WfbZUIffG)"
    "6ekIZ1Bf|1#bj^2*B9j8kCkln|6egVscgmVC^iRD$Q6V_A&x+namF9&DLe5SY;QWV-oQ5hAUNGGJfT-I%lY}Lni@PBWdv(pXxF?A"
    "ErXQ~w=b-ax2a!b4GqR9U`KW*&Z48$m?lZ2B*pK2x9OrU14Wy-mG(y4p)m7Gx8bZZ-_UyoL+@#11^(+#hWU-Y=ilgi?r);+eORy%"
    "1wFWZMK&Nk9z^c<R?P1f=b<}@SL%cIeK0J1ly*$iJxP{_`19br>X%Bu$2C<+nRhKeE=}k?YaVavMtwqaJ3A@FD%i&ah%GT1<;jwc"
    "g;OCa?@kcU+bZXvv|eyLwa3Fw)d-<M=n#Ie2~%<_M;w2HLc|dYrbEXr$rM8F+d(l-yZs?5d8UcoRqQ8U;d@J<BRB|4dp>)qV>ujs"
    "{Q|`I>$V#d)~@(&Ot^O&v7Ce{$kcmF-Av}KPUHpTDHV@5E0*~!ei%f^%?jO3Tw`IB<PFXsLVH53lZ9>E??=&E59A6MUnBk8L_!(F"
    "xtd3NEda03H7VL3xwS&{P+BOx>dPCNkCCI2_Pv_{Z?<l9xo7|OhNBMlC(mu$MJO;(8Cc>2|5-2Go>@YX>t40HyV(GSlT}sQ^p;x>"
    "9}EeGOK_k?N!?IWd`=UjyOM6DbaVB`P;Try=>U<>aI<q}M4`Tri}6wuV~;W0O(1jZ?%nqN(vFfUA@{d7kJay2H|1~11bdPar}j{G"
    "*IxIlMQYr~`J|oG*76jZd3IB+;mRzjxLn6CKiKlOWRQHM<16WyK8tADo*mf3N%wt)<@X&*_d&Hl3mxKwYFQ_K<&#bD>B@%+F~82r"
    "K|5PpI7LDwIOSy6OT0@3Dep5eXROVP<&p{%fwa!opaw-Pp<4HFA+nR9e}9Y$(DDfFsKWIMKa#P*)xVo3kh&Gs2BQHVac3$K%$${*"
    "u!BcLJbNNQK5GWT|AT8CE|@X}XrZ5%DqYE8!2FH47NU`)OYK%)E|!8_Uo;0>Vv(`sGf)rd8YK&51lh{*_BD4Zfb3?t9_D(bIvo1T"
    "POfKcA|^hng^%43smf}g{XgHb(ALzEV$Q3Kd|3qUI9#B%t}bPYJ+xa;?;Ll5KfCQm9kKC<(yYk=E-2Si8mrMQp8_ODq0*}zhr7iw"
    "*FBP9bAQ0+bkKhchod#=YNNSeSFT8A-Hog~w`S1~7iZIlHQ$UfyUsk&-s79}pbhUETEg#VP4GW!(4Cn9Jsat^&cAnOlr?$$hXrtY"
    "#Iw4fP&R4PaR>f+RYq8VKp33yeuNCCj+793T|m=P5-9DA=9qV1BcY$m6iNU5hz`KH$bfGUL&0mYtPvd`5I$$bH}|h$c;oE8fBZp!"
    "0Hp$+_W(+kUZ~?F?`bF1*!)ykhY<?#juKGIp@dxtP{OPj#yrIuy^}LkA+!h~gLsD+VTv<;!NF4BG4e+N0)%#JxsJGo*&!0(^QiqL"
    "b!|INrl@QnvBGhd+I2EI;UF6Li77TyNih{fuU-d|RJ5bTwHNC}YX=oniFzz0h6(J7N%OrTM`g9lMz3n~WYo@~*0ZUN4r1Zj@1n8L"
    "cn)9wBU*r1F?92_^AiAoD9k*T*Hq9GE9bT+*1#Nk^9CailYgTHEX=~j{==K07OYRDwe3d~0cnumRlZ~+VukWk@@aAAD!t$eF-;?B"
    "$Q<50L7t{JbvCFn){34Bx?~5~9mkIO)x57=(sgR_n($B<%%Jf0cn+JXzv8B17eTuBo0<IE?1w_5_7Pq1ZV+F5%_3cDt3;?oKO=Hg"
    "iP~)A)&+vGGY{QYj5z{|N6bi^8U>cVEiq`|M8!Gx{1k0n<bfOuVrFUz&bYGf{m#@STH;q}mMdy^=`Nmvfk3&!*amwp@|!>d!|#t%"
    "7DA)bx2D)f53bau9aWecqaddpE?BLl!H5)yS~nPPPnV%ozml;5k@MJaL8T(Nix}XL>eoaw_$Qu!hcJ+Lz|R>O?|2vdh&mu0W=M{h"
    "6K+-=BNZe2$eIqN?AxIPZ)SYzwVCKre%n*vih*O&aw%HNI%WK-M9ykQawMu-7ILZ?&IJAb1`8I8#3j%f=3KGPbKLSzYCob8-W|rt"
    "wrDKi$MK7YTJ)iEdG_L={OX2ASx_;_VoA?@gF|-LyN%0UNGB7S*l+{)w)JHv-tsJpiDS9xB=rFPXG{cnxO1SzDdO2h3PjF53zTog"
    "@=m<s_@bT^3iWSJj_?%ues<W~G{8t)xK{3Nd@2KbEyjQ>7oTGm2)JgJ_z)Oz+$m%kERIE1)ZwY~sRe~R$dunb6PD^~{J;@z8WZN~"
    "=)7)%eU!RW067PL4OuWdjO~vj$zApZzs-Ju!|=>H0%fZ}DRvYRh>owBR8IxD0eyxW>LyBwnNpzCndc8ELxs?Jwax_~53Oqy&(o2)"
    "i`NsNN2MSRR)K<yR+)8n4>dQ2y8tm6g_5EdIGhSz2eb^FFRt4h__xxi_9K|#BXe*eGQO3N@j%ajGS9f9!^<kjxf6*lMs9`|_f#Lm"
    "W`i~CB4&*6M{%OX_<DBuwvOKsjW7Bc__hGwqY@OWC#XOG@kNO>&=o>Ww8D|ux2@S^6DU4silRfwPOm&ZU#K_3HlgCcVGfmw_<X*9"
    "e3<Uv1)pIKf)VE67pPbH<&Hi9UwA&@h_kOx>z}1w?}Ao8={`~!MSyCr+|Saxtr_OP8kV*H!+VhJ>;gXIRS`nRUigM~G6e(+cPTwm"
    "Vu7Qkm2(5E>mt<<==qXqXAl<1opdYTMs7OgiJus%jvf;1LikjWUEz;+bR{$9fi-*>!doi*UZ42gzdwA!jCuI{%DOdCQH@?Y$sku4"
    "l3bY7L$kpJJiQlnK`d%@t$ZmMNHN;t2L(9*V1Zgi1uN<iI6+Z3wU(K1bXNws=8A~D2ESftpI(*7C$j>am$^hnt-5vxUd(&*jt7aK"
    "qYD=SvuMCwW1b^HmeNS(&}M(7G_6{M>nnZ#_;M6+gvIV)S8jB1RJAU9&FBZBCDW|omZQ%5TA0q>lqrW~cRCO)9c#4D6ZVx6uOA;^"
    "n*@pxx30H~mDaQcCobD`6W@(8f&R&xJ#M>E*NuWoMI&r2&Nt)1E~`+fe*QX``0If>m1-mziW%+`R5IvO2fO;xD%W!(dDj<D%w>?W"
    "ZhN_Ghz3$hiziCaSeWuX1KD#XWWOaAgJi?o5+7(WD1_;WiP>XpY|pQ^*TbrdgMqBa-GCa|tlP@#g9H4HIn=klT<^keO>82K*$-3$"
    "<Il7~K9TU^074@3Vkt?omfhhB&P)p^Yd5Z2*5%C2IeBILBz)R8>bXaYtiZz!)PA7k=~guy8hHzs1RD}C=zX>1Q9ZENO~3=Q(?Sn^"
    "14??#yem`q5h<a|EJ78KA6%?-u@-}BZ_ozC@J2hp0v4`daqab9QneX&f<_(5?UWSs-ED4mAH*i4HQ8-DObWQfgz?thp&fo=5_d0K"
    "dR2%`l4nL<Sn%Mz7tyoOc?!~jWqdt0V<_I3D!pri=YZY4_A1x5i<*J>t)9)_Tj$7rwT1#`V<hA%_wC_8WI*iQ<g_(#nll%E(XPN7"
    "Lj!wX&PK|=dyGmn<vQ{<6E*;9F37jqW?m_rH>H6Lb<y3e_bhY|jPf(Qf;M|I)P1?<MQ%EpafmqWmd%WJ*TiD#t>GTw9Fa>45ebt#"
    "G84zpw$wWanE-`t^`P^uF(n(2#Icw7pT+)0UD=z$0Y5es?ZLJ2*gOET<INO3cFjb%{)xP;a8OT{DeH5*Y0SSic!MPZPCTT%=(*Dn"
    "9f(d5f;1h2`OR!1(R6e|%aN1%8#jN{{HfD^M`V08=v~2I{zjgN{evg;-^|#IUzW1#lnb)6a3V)Ttw$O<yJ>rIo>GDnKqU(CT3rUf"
    "Prk0Zv(1g{0dUf#gzD)nFSEsX%|gx+5H9LHC86QqV$ib-jPxRxc;-!&R+3y&(jlN`tXu^Jf8xWF@Fi6iPoZhCQ!v9e*dLP*e;VC|"
    "J$!2G!-2v@Xd%!h<0S9SU8$Dg+IUP3%ziZd<uTJE{LdcyqqilDhz^rK#Axe3|6zo92*eXC=<Ysa&gyOYk1uV<-F3?5XEaxS+8@nV"
    "<l;J1w~870!ThG%nVALTh6N3GL}A#M+A%d+E&@8zXoFm=N0!25I8``Iazv(X*0t}x(@+sJ5Vs+(WCA+y4?b3UzS#M)pyqG*ZKCGu"
    "MBrs{gWo3hp0)6DR~EMTOT@!U3NBS64&>*W|AUqJkCySjz2@`ZT7t3Yp-OFE<P_h<vPgTf3y|pF9Z-c7DG;w9Pwe3eH~EkqMG<fd"
    "1axV&?^B=4rgqvitbl_XP_k17!qDc&74ZE<=my~O3E&DeaH{Q5gz{FeU@`6VYWHq9wwq5F)N+QB-Oe+`&Z|vafu5NT8Ox-CZ8)Ll"
    "*4r{>^vKWU$16nf*VmC>BUzsCf+*|}PT3xt;dK;|W^gi$;wSWWE(a$FE9;Lf&UWC7<Q(`h4IJ52s57n9@MCO{zHd>&ry^;zNR>jy"
    "V^e6TMS~^%G1y+rTS1mz@xv8s$~j;1aczU!nUW(=F750oPYlrcZu35<qSRMQG#=Jz-v_F6eqEenPd~If=>^KMMC@O>$QSIooWo~v"
    "(}?XyDSCEhU<v63Lbk1tZ^VLjKB)cNds+7+b4z#m))*b(`O+53o3foNfsEITGx?p$5}V%H#Tu%1P-W@#n5HD_Q&13Tz+9pmJWJs!"
    "$yt9bu(gdRP*vHT)u`(J%WVFf@ZSaR2$Xl%vL9W0|Fvt|6)O46FU+nj()m$lW_Io5yYnolYaeFUTBQVYI+~?-I)AAT%&y%~Qfa)#"
    "3OefA0q$B?`oR0Ue0zipET8nac492>dGAHz6IN#+F`>6LR|#k}%hn7?`9-^dy;ZF@&9(oSwYZ|y>?03Uw0cED04%qdjhS>AqPjZm"
    "q`Im<#zwfec<9BQdtD2$M5>x5W;Q+jvFu9-FEb7&ku+#tjuu606^{r%a9iA*+l*DAKO`OHTi#t-X-c^%e=%W~8@^4^sx31&#LSBc"
    "5^f+bq{){fO}yMIBnM$i%v6K8O(8Y4zaI~54qk3vsN0q3Eq<A%^n(eemRZh(sV2l)thE~xQ<L!QDK*ZTIQtp4Lb^}SeM+R^WQ_cD"
    "5sVYp&xtdG$n4(e><rH2ggMU;UC1W9Gmb?5%a556EzFNqh9`Q81DT{$#QhD`mHF^LD@bS=jLLulHb3ki>paR5GoOM4xZQvp9zKuS"
    "{8FPB3%l>pL23ZCCNsR{OHq69TZ%aMp?QSz%<PjSs^8_vC5O;5+G6Vs>R#Ke7u!uJt(PC$P1ve}D)cKytSV%4d28-aQ>Uy#78$d?"
    "&2@_mwJ#|h&$_*athvI1f9clTPg{>zf|@BHaO4ZYc+tcj?_63|KX%v?Ud9|>;%KI&9^krldf{$&S1GC!h}?!R8xPXkaqd*`KD#ob"
    "PIJJ23XN}$awAR^PsJG!o9qdGQ^Ss!{>Sp8*;p3)vR{R>yx=D`glIWV)=Ln-qQDyLmGk#56nv4uOqVE)Pncw)Q-+ziyW<Fl*RspO"
    "0Zy}_{YyK-1_@`%KP|EFvjf-%i_`U@PkdG2#%3dt2tvQWWuU2<Q@j`dVMKk#$$Sl6c9$#T^Yv}-RXvxfRFXYI)%W}W`SAsIa4&O+"
    "PN|^-_<B|hYT1Fz?AU(rw~S)YaK-~ziz11M4zH+c9vC9_zW7t81w-5_lHDHk2pjj6V(hZdd+lpc5RcR!R93c#h|Vei3d52Owg7W#"
    "Q-yFK7g(AhH1s=!2AxbS6Y3C0z`)^;7AT%hOguv4qDA9#SCkwa$7UlGjx$C9`#CrPIiZOTDY29EsFg2n5OwG8B+w9b{YmGg!^t5*"
    ")bat7DZj$A4;Reeyfh<fzD#Lop47&={4sb+=wMwNYJgw(^nkZxOy^AVT{#alEA3a(CGy^N(NBm|=QNZn0>L069_rS0nrOhUqoZr&"
    "0w%sQ&XG*nwMX5BJ;F~^^ZvtKXj&QRyAf>jd9-<z9_g6-l)ll3N;PIHII?3PpHua#bd$$aw(K1L{Q^`~=eIF8?pmZ9hHbU3a3<>X"
    "eO|(cmWM|(swh-S0ob2%*PXCs9SFYmT9BiK8N2a8I=wlTLwHM6ZE2jad=fHZZazN>4?R>!N@ILt8j%*sF;yyBVT;9<;~y31Rhh9i"
    "?02jUwTw)H0y*MJj@d{YBwNi0#d;1@Yj~4R>xC3|IwH4Tml};DJtNiz9s5EVC4R=*#AZgYjrb0>;cO=tT5+L>RdbY^iIm%81l!;}"
    "Ptftu$N&WSrS+~)>GS>o#EDqb!+L>zo%Ob96y_Co`pc<$h96B^&1e=d)-vO{9)Z$RP)d`{1e4{Kp1G>92n{=TGuq}$GrU`sNWk!r"
    "-!k4;-+I(DwSN@^hR#gIGYtl>cWZ&+_-&bP6&#nPPdn#2Id>;Wt9NU@_{3-Q-TOqA(EPWZ!-EL}3jo|`e5Zwd9k1*`!nRD~ba(I_"
    "n(P{Ki1M8>f^Uq>4;V_ufJ`)2ZJ(&*nHx1-iPc%Wq}ExTjMbwb7oy(?4oSQek6Ha>>zSW6lWiG^G$9|g3)ia|d_(_o3WxdSfPd*4"
    "8GeaM_q$-R*fXz5`#$JDsMMx1m+z0t5cpU73rJ+vw%WRCSs=a%o@`V8O(Kg9kV-NW*$KX86gkM*ya226q=DiMIGhuZgEPXlT}E&2"
    "LI)On#o`Dio{mk`RbM(gW0b7z2y*tw%vyFX*WznuxuF9T0JsG2dUL^)>xqlWeDW%OL}Ng8cUJ9&7iY`WVHsBg!kKsP?Qx$GmSf_o"
    "akp?47Vdfz6@C@Ka95eInrE#(iNFWrazBd+&0E%q7$zrzg!r6&WJv;wKfc8b%b|_0C9mC<hf&T7^;OtYaggW5pew!`_I&(UgVT#G"
    "`C#ArGeAs+%TQyU@<yklIEU5djCsdv;gfesrSkr<Ecg-wG=B3rn5xUZc9D#rQFJE9Sr4AMpxwisdpr$C!#VVJua5ne2?xz6olhP4"
    "V_D>+`fpYalL5Jgz1C%fR}^7)pZuZCTk^iZ8gQv(@Cf{J<`690Qv%!(4iAvagpSar9*0TI$ef-up4~dJq+^`p0c*C=M(&jPC(j3I"
    "PnXA);P&X3rF9^X-T5c)OYiF|W`{Lnc1Y9h0aC}uhkX^0#{F@@?e2ghGmozuJBHpmpGM4%?n(KF!Uh(&Mxao?W>G<S&!4(pTo9D{"
    "^h^m{Wf$yPHiN^_a6uQ^<QzWef=@(4TKQB{^s2@QD@aS@B6$azjyI?D8N>6VD}U{~-*zRA;UR~GG(Ih~FpH+-?)U@U7EdKhEm5_N"
    "K`ia)BJkB@JWZ7Z3$x6Wut%e4-B2^&n`S3)Dx^gm_KkuRL$H=g1Y>Fv0sE5$V$Hchz0F|*2&xlO_;1`|M)Mfibw&JnTFl{9vNar6"
    "x6a<IQ^1~<bnn_<K;>&wJAm9Nd5x*wP2?{p<LAu%itG6hTm7+W8E4?MPqZ9B(Ri0t8&tghvKnAev~2+R=w}T0EW3QHC^uy!wq)|A"
    "#8Zsp<XMHdwx`jF{2)_vKk|;upgL>#d8+7H)k{?~#D_M{C-rgEQqJ+K%HkOS_rfa@IoHs~K9qB3cHwz9YCo@IO&S&;6-+1yc;_;<"
    "G_H&GI)>k-d(C3MZ1V?3)Trf6c#77)HIv^FKR+bgZ8$L{oCNoRunX@6pPPiSd;BWlKKC0G6}6OGr9>Y|xaCp_cMzg!VflM|+GhX|"
    "qS+_2Br4x6E6)Jrw&fcBI*rmC3AFg5U!RC19hMnp2bdDk2nF(gC^md=u<BN#o(e_takWwjcDu`+0^n!5tJq-^!`8k^J+3#3pSh4b"
    "Fzz8<MaEYO0xBBq72~&92q>wCJLl-{ilO+loB1Uu2=y^qWEc-J8O4ub!^bE$DJ3+;HBbNe7UY4{UY1f5kt9s;E%il-!>6voo}E8V"
    ">wp;@^s&N7fH8lv?%PjkmL>z{>t^isHFt!IX06&0`C=Q9HihBMmIx)J#Y-FXX_Wi8Dgs|r@@YJC7{Z$)vtxIcb0N!jZNv$Et+1uK"
    "N;(N~x4^#Ez$d2C`zBc1sa!O$qv%5CHGdrg7Wh$>IsDOqbHDcrPi|#~nA!_%TW;X&4X~*lC~yx3A$4wh%3~e?GiHb*FDAGM&6?g*"
    "zDPEhSd1$(K!-YRAZ}9tVZpMSsd(C>5dImZoIL4c`FU9#%i-<@DBa!jluZ<tgsQ=pusFu<fjma(ve*9OIyLC>gYh+~uKN{eM>SW3"
    "l0_-*Uz%2-A36g1g=|=a_Cox4M)c5E&nSyTuRu|c$HddFX5r$`Mv5Shj2)_I&xBT?DVfPWwzkp^wJvf!(DMeg%ahmx5_dVWu?UE7"
    "pgk<N=C(LLE?>$_C?3PX!BDA{OGYHo`^9M9!H<u4Q9i#Q;OwaZ@Odu<xP3vDF<0o{DN2jONuO&TQJS0!32daw>~XK2mL22sI0=(b"
    "BhM)hXDX$b;TsM;A08rIFRb-MOU&Tu9pfZ{Xht`09u6gpHzSKamf#y&P6)x{J+-W9)(S_7$CC;YR@F`M;J5^-Kum@j+${kzb9qNG"
    "lx73D6#}pzJ2cN-uoJ<wNd24{V?-Ngle$qgybJC<0@E>ZkQ=7afiklI(mGCmQQ<N+oln*gOatG1l*9S#u2W?oQB*jR2ExjNG+M@r"
    "xmNXO?<@7YmMKWdD{PiOfl}&XTEN<6mb?{zNx{MY&%Z=Qz2-suCO((tEq(dhm+y$9&##3oZgJ~O1CgDqON@a*@>3x8*dX3~Mm2ni"
    "jMw~%9LSv?*kBnTZe$<HoTLAZahmr<&1cP86amCar6qiuEd}^pnn5j~=XL+>XvQ9~I5g(h*rUa4;;pKway+uWY@3d`TL<OjyYj<d"
    "9V#e88Pn8h<NrAJ=)-`T!ESCQp=8K1?9>;DiLFrnfsXh*h?kalPFkYZOcjYzvk)?JG=O9xA?(g)0nXRBV19k#vw-BBAcwDm@2I4I"
    "4xC0-i-}J9ge~Ew{rgbsuXrT^56U0GoXwCW@g1^60MmtC`ADiviQgehJPBFiKkj|UC@mfFuaKpWj?$x+j8kSbN!WuwO=ZQSoOd6m"
    "2?Sdj;U8b2OGffWUdOpf3H}1N0Xk^~%D(<Q6&&s?wcosCiuwv;q6wJ_P94HEE9rhkb4~3i$x<IB%WVOnt$Oh#$5XL>rQ-j6G}9aB"
    "LZyqvM>!&PMkrD9*al+WQfA;|xT%jjwCg6eXry!fpuzI@RdR&l2%Pd0s<Z<m^JqsudPRKI=&><Mm2A=zyJH|7y%r3w>Ba@$mQN4b"
    "wd4%m>p6zK9?qMeeg`_SAAwGPGC$sdPU1Vz$!7#Q@gIRs!moi&BF>}0VUO8Z3g#BS`vEQARH<_8i#z$UaD{yL)0_|y{kYGJfAZ@Y"
    "&f&`oBPF7An8z0G2)^+JNH<5wz7{8!Q{&hwQ1Qd9WZbebqoGLtnGa+e#g9rBl&~(Mhl=?&R0s+q#;Iq8;`*cEy11Z_ahD~mt!({4"
    "6A7x&-ST@5d+xc?M=BhUb#AvPvL{M$d3VUr%q>~@vZWcQ;9cgnomj4$UA{!V`}(^A3~3(8fx4RJqc4xH2HmbIm85qb0|w;^Q^yBa"
    "Oo`9u>LZfseW>lzzqDW8-OK|+y3%{q@7TxdAH`d~MQ~cS1B%X94n`Uw>k0wRx?^cz8*eJj4g9oKUC<xnQcaLOQ#aziXVYggbArQc"
    "rcd#fvG;4zUNtS?DA4*r3`Z4_kzi47ZI9+p_`-olGnzTC!ZW9pJeIt##m1v*w*$p#E9uZ2^w<ZCkqdlWn%`!IWr-xCu^w8?c&*RK"
    ";}pe?^|h93UJ;~DUI1>Dsz=i9JxfK}eVx5`QH!*w>|7l{;S0)B(H=$_pl3-$9-l`X?=Q7s8_kWIyKO3acnzt{Yh_wlX3c>u{ic4U"
    "m|l=Z&A0?3)GT#%_N!O(`~%7jYU33itM#(r*en*tlBSP0M}0Yb@LS2P(=VeGtgdX(KCgipoP@Ebei}%o1?yDqou1|Z++rL>giU2<"
    "N*K(9cCIxp#Ct^oHN1CDXFP{yH@|iK@Dr{Chv7lM`KyhnY~EUQQic9=J0eh3G<RnNgs&e%rtVO!)B^qSM)MfQcW28NhkBv`@{`)q"
    "oPa!HA&W$ow@ww|?{itTRvbY!*5-^W*?CoaO{OEbPdiFb1%9U0j<eGW9QkgXq8o`7$iMF0&Sg?_1HlfGzSnuEg3Ro-K%-SDHwGcJ"
    "EyX#wh_|0usKT}YTQwF>s?Xw^*PbDt3j6~jI*fcct4o)t2r@BFv7fw-6OtrGgqRV73Hu2J;K&sm<#l+ir%AZbox^?eiL;eoLsaop"
    "J<@8Ip5r5o^2-s9!11x=@G(HU6{~1OeMM>`f}MFt*hk)BeNw5hax28OV@1;nH~1L;e0Dn-cPggJ$(|8M_SqI#eFz~}`31;s4hJX!"
    "?*(Wh3Qetia+Pt;cI|b@HV_M@7iZo9@v(5Js<-)*9I++UTMub58qOdBgmWZeQ#(y7#jLhDt2XjO*|2W=spxeQqj!fHi$k4^Xfq>Q"
    "wjOV-C-@M!Ns$S=UW=iv91HapY3t2%kMT3UqRbs2<6nssZI8hXcMmm9u@gNkj!HrSNz2-r$O^|OBRB>M=0}ERNU32)pqW%PM%)#J"
    "$Sg}=Q*J$52gZIAKniVXU3b<0O-8=g=M(P=n6th3shlv3>q~#pS!n;bf`8lsBaRIdrE!@1<X;rmh>SI@Izh>g1-Rl40TrE)FVTri"
    "l`f907Cm8z*Lae`Vdp5ZmnI_r>`o`xe74DNleiJuh8!$3M|3`XruhD0gtqzci2AT)LV&c)A%`<*&b3#^SED%Y63{6G6=#5ixzN@6"
    "iehSGQqY*n9UROg09HBJ5fg_K>+q#kQt%Q^E?z=(faU%bJ65tq@#Y~UfIeA)>YDGd6d7<TeFVX=M7Wzk9jbe8$H((!Iq%j!5)I|f"
    "Z4nyOXM0qh1zJ#9eU_k<-ue(C&)d7On-z6n6JDIQ6bY;_B3n@~lc0rJ4moV`;Zx$fcyPx^DN5FXOUbh+?VDR%*(11S1nvuxn#p_H"
    ")&_a+k5=I}KUUY(vfKy*GkT6>pF-vV{IJCJB-ikv6kJVi0vIp$b6mt(1%tX?KoY5pEw})6wB^5FAo{PST^%s;<)Gw#lo@6BwrgO+"
    "S&$kydR1$^$B)L&fd1?rL>Fa=8FN~vGz5u!o8S#Dfwr(Uj27t*GVKdSL(z^vmDK^d35l<UqQN%O$Lf8c^xS=%oE@%+JYGH-G$Iz{"
    "uc^nq*6j0^l%`djPR!J<LLd4?zHUb2=?$mJRI;SlYWL=Emt`h$sJ@lqy!*VEDbV2OB9lnQ%v41KIJgsXuEiA+tXs1jPd&^s3%@s1"
    "dt(FOWmS(>qcsVIEuYhd5efH$LM5SFwdgQF1FP^RWsf~PC`ok8@DIYaD2H9k?+i1M9++>=zE*W$M)Cc!CI~tRW4FjvHCf}$OB(73"
    "C%<t?H-Yk;mGw*7H3x$9%#ceuKfNBy-Fl2%ra^ASI~=tdzJxYrsz7Kr(dCz=7mxk8G(K3r`Oh!S@V~DSLXtq2%v|7>eGBE%ecs5L"
    "8GwicHzFxf;stQ>t3GeGfU;a!-jgDudBj-x?&vpyYE37O!13*9t{XNOc0?k;5y^{DOhQdIGjS`qha{lK;+Q^2AE8dM%;%2+*S%2`"
    "7AR)e;P+Ics8Yw;wXVmrPB#-3ONG8whvT;s1E{EI6E-j8hB!~Ig*h#X25^xJ-fSs4-;9S3`}g;+*2M!9HS1Fi)9j?r<!c-#9z%ky"
    "hxpqOu8NW2rqE;HYz%IZtuq6@1+qZarz(1k_T8`ZjA0GNP>8Q*AC^;=kzCI_%=p5u55a`01|Fq%eYZ%bp+QSrwgnC57P<fh@j9=E"
    "aUkw{?<>e)cuGp`xB><dE$6R8!#za+L39peFS;U5(J1Mv$A}m4aaDpd#%lLv;n~O6V=Nx<;?#35QLHao)WaS>;u60{gdMLh-R3|E"
    "))(!>EaJ{o$)>+7fTse*_O&wY`(9J_ewLkk{+vRIeEl*4fp(G}Pfx;@c<EW&qY%oFgCBL=OPu8$6sGePPBP@osQo5FVj<coW<|n|"
    "3o8$DKM&yg@PQ)`=9&aD#~hE6L6#-&dTSV!2m)s`GJqOs1~C3y{MD6n97!Jg$JeYw(Hn#?M>V8x&MH<cZAWpqfK%bJpi08tR%SfN"
    "uX`8;5K)sK4z>k3W&K-9D~B~yiqpgZDqD8Ntgn%b07x;O;>PWgxidh;fX>&#^J3cD<%cK;UH|8S(=FYg_)@>X%>#`*C=448d?rEW"
    "No<{vk?&9nWh3DPHe`*+M;~V7BndFJ^2ND$|M*>0-;Z02AV?qfZt0v3h@&Lc?{Eu14@QfRu;V|fPk&;bTmfo#7l4%OLTOnlzV716"
    "lKM#h#FG<0_U+r#MUlW+lGD}@OSo8dmJj;?O(*6kgv0~qe9(Q{3_bnKjQ2{QP+T+-Us4u{to&mh8(QB2tryudrelb@u2b92thXtK"
    "2c}i59_Yc{)!U@p72|IW=_;kXyp&+hbMw)W<#9GcDS6@#LWabrfJHwf>DK>LeM!6j?B8EjU`AMe^_TDH*=9dG4SuecRdRh(w~k-t"
    ")d}6*_E-}oxGY{L)1DByjz%rxZ=33ExUR;`&rQ}6<2yqdPWR)5?%h{>Y%^E+LJIQMbqKSip@u8>OxUmQM9jho3=;XTpiB%PK$Z@g"
    "PqE=vOm(YtUweClu2a9Sot!l_#1lEh1IEGE<_U5RvHM6kmb$i%?YYjSWiRJ)=hhVwZY^*vI=hkBasc)cb^qw$=rAzXr+?|eda}iM"
    "{SI$lct{@BcO0ik#G7HNqP@%IRg+zMt(aZS&3a6`MU=~%yL6l5=%4Op**P%9h$jQGw?P>3Kn2lJ4W4M+awor3-X2fHpq*H?J2zmp"
    "qcZW=t?3wz`n*3VcY#twEHo}DaV&4-*kD)O#r<nn4Zw!py4J$O^W5`WSe?Ix7&#U)V=a`H-F-8<VNmw@66K3z+DDBl=+7$K@+&`D"
    "4!Z4oBMjdG3Oz&;_5g+YDdTG<?jpsP2QKF(SbH9upm(N{RZrCLuF$NWV>czU(cV3oWxKOuAiQvnkvS7PBCnQ)6@quzV4|gr``v0R"
    "m^Vj1W*j?yx<{ZQib6C16%}T0f=eVIkLHm1qYmlh1vxO*)3Bi^dRunZ2o)S#Z%E&n*CF^hJKeYIKi1iT;H(^u-A7~^!^wO>YHp9A"
    "JR?MP_V9Dx4m*5E9%`W^eeA!`lxut%u?R%Ygz{mPxC)Vd65KT}4v-6$aDcF&T4TKjQWZ?Pjiw)pJ2T{zBlC&Tv&A<DEZj4~>vOfa"
    "j_8+!eWUHim&|(A4MXAI=<AouAl&T^{)<r>^y2URcs4yvj6W`wO8IQuJVKc@ok^prKoSA8nUBj?{g(N>`RIRqwrbZDjZ5BcnH0-A"
    "GgejKKHqL(rnKufMry-TTqEye*-{Ix3%XXrNF~G>nQskeQK6PRmj(zu+t8OGAzS6A*C|`l!%wNe+J_l@jM)$<kUWdVKa}@0_K~uX"
    "R3JUl24W6TA{466^Lsv_7AQ@Zee<k@3a%!_9M|vcx@qzWYG5-{Z_0E}vK=LVae(9Q(0VHyzgd_1Qym<xL-qh02=-G5W1LKIt03G0"
    "189yO{i3de9b@m#7jc?}s~WhaH6WoWj7&MDVsRQEWdvk6be~2Ah+ZtT8Glxgz7MXu#WqDM@TYtf;E&K^ffXd;mYgkQw7{6q5-W@P"
    "C!B-gCKpo1A2G7br$zcP59C|5_0B5((EyU`!hlr&QeYq%KdKVTP)YscC;p<UIQX2MvKdSJf4JelD|koX@;?P5U0|}R+<i@N4yZ$J"
    "G~sy~>S^qeD~qDKo+-%BW=C4P&z27P8bItzg8k=8aM#;reu^SoESq}&eFxg23pj|wHB>iKAl~Ls|K3zOI-NGcgrZt>oPzKy!&?-@"
    "phz8!sG;D6qB&{_6ku=AmAKuDeV0D1o;Md2p#dg~s!K=i(|pQm2Jrs6sz~RQ*E_YfI9KxeqCj38-*A~XdXj<r?i$5I8jAw%#m&U;"
    "D)^Z8q=L6t|9chuM=j_Z!M{HIq5Q{pUb#eE1F|g+Yiz`EJ^yaO+K3DG{g0QybSL`R70sG*=YRJ%0sV$dRT@sD!vZQ|!{rihSt#V2"
    "14`PKguh9h1tX4BGq9NZJU}t~(vRYTZPlVU5lHWQ@AF7+xM`^RE!~~~@@hL^EVg+98M^lOibD&5&8H|7c4I7Ub-JkR-?zZsc60yC"
    "-E$OQATu9c-?ua-9>3`H9#pIGqJ|IYKVz)y>TTKF0pjisd@Ov?A9F!%aH+m$M<MR#tzO<?1}W3O$gY1|uKc$P{!r-Vzg1;Z=o02&"
    "gcd=(pX6`JX(s|@$RYjlw*qy^Q#@T+8h`71dQ3gFKrpQvTuu$7?(`4a5ihvKS8MA=YSsb&EjcaLUGqz2`0+O?D?jYfp_@8?{7vx8"
    "t)MWNOg{cb`O-~%!20<&)<<JU`{&<`fB)!jW_0wgvhA`Eo__3<)I}2}nDOP?hG>c#;dMl^AYa{asoKMhJATzYpf$$Qy8@4AuUP7f"
    "W_3;~$T}@?kgI0ndIkI7wsfD3@@56-+v!T!C08q?f_t)B`Vfxz;5{oN?j557l%x%B2HE$=qC~k7BHM}|`xkHSUt;T=*~Fp(I~R>Z"
    "%<9wFzpnV8Gwr?jkG{-F3HgzJbJRIU{W!u<9Km;In^d7OS)<HV3_eCifKKc`(X9pE<~{(<Hbw@3ZfhWXXQQ6!?quM9`tW_|Sl-{o"
    "RUNej!m6=jC?A%&7II2WP&%j@wP{-iHnr2)1j^Qcn5lTq9D=Uk)GuRC)0-jASalu>;S*_p`_K~P=sny^8zxTa!!P!&=)X><dZPWM"
    "Qjhj&eVwf-E7H#2I|njEVyt<I43SvLyu5vu>dz*>YJOzR_g>DF=y81M96wZ$zq&Ldyx&7Cd=GKr5dU?EAE94|7<DG1!1+1E`OfOE"
    "hWONmVq@*hy@$9Kd8}mvSxJW2LlriMt)9b~46)QexYrKO1b~MaVNr%Coi#7lLp2(<Du{hp)AtZZ!^|8{P=D*$-^Ac8v-p=2fsW`("
    "(#O9E)QWPx``2yH9ms|JPcxL9`$Zfe8*p*(dA0ec0dWX!Oo^Pxlob2$c+9ZI)`|>d1UokE!X7zDK@~tv#p;SoBC`EcavzdjV{ayc"
    "+=^q-NCn%)0NM$$^Tw!P7k9d$X#L#1G-!OV7d2pP?))4_xxZ%$3IgPFVKWT<+c`|rJf&JTA>WyE_F4oQhMHn4c$htqM=MqIFQONe"
    "ng^rw$SCid&%&_eOU8KO#l{w-^01<bC7B6}VhAakRxEUsO=G)?_@7RL0h~nJ+{3WOB^D%_^G2=Y=|^)5Ejg~YOAf<1ypOe|o-c2U"
    "xWb#>U|(R(@O9?Xy44-hhWeO#NbAxU46nb&=?p)QWN=97elz_5YnHWM;$xbi6R$T%^8a=PX6QTri`>E^iwITI|67+Sl<H4K5Kv{b"
    "$g)|)kvzpz8E7&TsQmslu~CPj+P(V<3KR{Mk>Q}g-2Xn-73;5jkMwvnHe=?$d`{4sx*NwIf=dBXilssR%3>^G4Q1E!U_Vd8y`D-q"
    "C?~k9%@!!;Cr=>Bm`?zCi?mBQR!{T2(gq#;Pmn|Dg_75ui9-qdoU-}cI+Qz)dZt^dl6EB*1Kll!Jy+Z8;qAG?&aLpw9zPh)tzZ3L"
    "zq-i2y=X?rJwxFyXNX1#m*|mH0OtxpU`fbFKSkSLHLfJ@drhk_*kcYC`eEv(3QqgJA$4`RgvjFHZ@Z2k<qL{z9ZmZfWUulFou;A8"
    "nMw=uw?aXhi-N>##qO-N8bZGLE)<uv4YlVhSq1!)-Fj<odky5*M}U(W0e;@GYp=l~p}mx<9i(qdg>aQ5xQOh%#P~bl9c~%K(%A(`"
    ";F-A%PEgRx1&}zlj=HB8^GtP)!RAPQcu@+dphg|n=p0-m2kD7`O(CMkp0mt#96OYUxL-2p^IwZ&k-HfADC3;bVdIIJ1)}xKq>_fa"
    "!hp;ev=&3rrCf(Sc*?^1(>I-XzeJZn+I8(CW&i>si$#am+#uO6r32NR7c*w2;A2`32jhRZ5#d;0-(!s+24N$|1x^$(LJ9+vntISY"
    "4Q14!h}eE~^1Hkg$vF#!=qlOu@4R)2zKIyJj-u|E4PrX%LJ1MEB4n8a2XZt*E(aA&st00X_4V34lMH}Gpj}hdqeE14?n>k$Q1Z?8"
    "V?;u<OY?JjF?LT!Q^XJ4#MG`x(HbYGZA9*{(Xb9Fpl!xY%V)Oi_IK(BoerUXM}8{SoZPhTMu;bZ=HGHljQM;kDX^m(4uTu|KoGf7"
    "^EYh`378$#>~o!%N&h#;)MQ`#_ICazb^1+JCbz)1>+^%aAO2ti-JJj9K-Zv8qEHm;1*Dq|{TKo7`?>5!Z#hqaKFDt+J?$JFWt;>!"
    "rVsu>`rOtqFlN`Q8J*x!;m{{E^XwgNPlw3H_=*l@H%Oabwf>R&;s@3|w>EeQKB01hUAf(WgP3XHo8V;=5QriQWccr1e!j?LFZe`O"
    "dH8a``w4hrVmICSYha?NbTHx3^T-m|6y@)-^Pc4cS%s8E%q{i?Us1WJ=Nq3z4L~Nn=zKu9D9*iY-wmFF&rTxX<Wy>hj)LO?d<1G~"
    "DRCm8g+>1tFMqtqWJ545PXm4yQ!;Hg-l&M@uhw*XK<=C;5{?(1rQtX+yV|j)%*HPkS6q?y8pw3yJw4mXDh^4a<Lo-XgblU?1Y4y2"
    "|AW$*{Oe~>f{to1s1y7;=LC`&Np;0yi1_@qwU_Wj1%lnAPe3}C&&Vi@<qw?2*6K9IS*{2(<|Al-6g!GPC3W@CEJ<L5he<t5^Aw#e"
    "P|@MB?SkuLm9$(^7yUdZ-MXKlr0~*+gJ60eZK^x%KAWz>^KJxCN}Q^|xAh`OrN{`qYV~Ymv#T~-uqNSx4i9H=oDjm;58i^}pI`cy"
    "49^|-R#icl=fIKIP9R4&Jn&K(&D!A>v_rSj4PC}yuVoe3z7)F5Vd&QdE!`Np#OwTOTq=I!=FA;eH66IM7pzLYf4(TY43cI9Ym)EK"
    "bk7O~aRZKW^?k(Kq$`$FBQ+i^cbWrP$_;Y#k_Ne8q!0`=TcPB3XmVjwlH(j&U|1O(;4?bTjgtTlc5b_{##td9f-P*@xFEBl_1qRl"
    "R&$0wRK{I!I<Y3v!<%J{`-BM~@5bUEUebe&+S1ZDa>;t4XxoW5;HFgDQ5naOcV^sI6tEYIv-0WA6~(9~AP+BxVuME5X@GRTD~5ey"
    "@)W4~q;KZUJieLAgy#aR>cruyD2|IM=tWKPB8r~vQ8Vti875(bz62Pf>q{ehw$`*PYGOSC&Ci7%XpkF1dj~0F7NNC5JApmR22ueY"
    "HEGdp+LHxzUb!?SeE91!#^9S{s(07cq4&FU*V;_piy7BBHKG{5!#EQ?V26KcVC@FnmPer5;|z`oBT<GvBAbY}mQTTjDewl3bf3`x"
    "8{xbZv$_@VMu<|^JTaa9`!|AGz}w`1<u{X#f;IaRw~(&RKF583OMZ^~y3D#fmQfB5789=S*b*Nq#Cx^Jg#Q?KG|)fBoe5_b3{=_!"
    "K72Ek8RZy9q&4%CacB1y36DD>zd+;OSm1FF7Ve3+BHuw42;5?XK;BQs5VQ%A$)OaW`hX)AO*8>Kw^{u*%C^*<No(<rTKOrKP`K2N"
    "HVDtT{s>69=<}U0faJ+GC6ce;IXaHDv)u+CyV{Agm9=&h$sx5cv^JfY@hlt<?uIL?Q#!?$hA?7^$ZL4j-zIqTz&CPV$=gs2a%(dU"
    "Uh&&3%yKX>8p-5;d8}iQW0;hw#z(z>yj%Q_ei+0VZw6J2x;MH-ull=}{;2dHU-k*LTEahLP|rO!k~8BBMQrR<1uy5p<k?{Ut9uMO"
    "d^>`|$f=M^;lb}T|86GY%j{O#&nm}$j7FE5Do!RB<5^|&CYVN-eIyFrb7gX!vc(%d{J>SQ@o>1~N?O7e@*>)~K7mYG+8eD3AxuMT"
    "V(@kR$>{!@KTIwUKZ%tkNku24_<52T7TH)s>NQp>f0>^!VZeh?8z|eP+QZZQE?!%Aq;oFkmx|@^u&6~St(UDHvX6+_512N8@iOD~"
    "5LJq@A|4imdlY#mD#;Zyg)`iZ9OizKF&6Mu_yf%VY<}o&gf%}U6CT+XI7$m;KcC>1>NdziAcwfWue4yYg6LtvL}B{BwS>37+szsa"
    "d&qb8?2;)@18y<_J@ZW7UG?HE$d#7mE=rHd;SCCTLb_pj@4)CA643ByMzfJ0m+zZH;nGFLRXLZ#FiNVo=i!UOkB=8oRD0z}&qATy"
    "cu%!V>Jhy!KNjBqIR))M5eFuP$<JMJy#3e}InI~++!cum^LuRwZ-Z}b2yc@A9c}18(eDf@6e0!0_sWQm>%fhEyCC$rgggEKErJ^Q"
    "EsZ@2sC4(E^ZxE{22;up<(ZDv;$3dkOBF_wNYvEF_O!a~9OH_*rtV2Fx`SLetos27D*kZc>w$-o>94ur1S3&&L%(G|0eQ%8`^{ue"
    "?!4~7n~?<+9prUdmq{zpU4?C3zh>~M7%^tpS%DD52tFGktS0$-5x;kjs5ddB?wz)Ajj3UY$Gcwvsb6n~iX#)*Pjm;yN6p?H$d5=`"
    "JdBCn5Eqqtia`_X(09OFY#7C>Ctf@MBF*6bC@*wUffdq5aS)>Kx&++Ba|Ll{@s6^qFN^zC=!$)JZfp8EK#vW+9uqGl)RLQw*B~jx"
    "1LEuMDHT_zLm~)z4HWX|j|lDai`6CO$`(nNGg5O=iOMCw^-a!}FKIS^9X$k4gSLb=n*9nw#3C0Qb;f{Hs6ZBvC{fXriVeF^_l<B+"
    "Dpy`riY_#tT_Ly(gESvYp<@*f5av@F@GTCXAHgxs4iZLk2DEFyK_HyyNRcHVVFRq2gL>!m9T0alNLPLMXr4l(qr*|0<S&zHTM=zW"
    "aXM-VL^-!xEr7hkL$zD6st*&w6-Koz$}g0CKtr8ksl=_*nza&C+&PIZqoLJv^}<7Kr32MLW18{W^h1X7&eKa|B3b`&b?fWCDxn~N"
    "%<R#nic~ZKD~&)cmhGam6Td@G=uw$U`mT5A@>DFGNdx)WYU!a=dta5}@}3dSxn^?2e2s)$yEaD1M@^&Ko4CQYVyylGikF3*o4Uy$"
    ")_nQ&&ZWY{tBn*e%#wqXD6B{-8rTwaz!dkQD7F@w$P2_7q1lS^qzzT~;{)&!xaHwMcGUg@bC^KsSj*e$ixThP6C(0r9x^?XR)+bM"
    "x2tvf(jw%eYOP*N1Wr;0%^DQSd0ikjTp8+P@jE$Y6c?xN%~5thOSz(!p^=cfXqQ2e(`OA=?0{IkodvwwMn`4VB*<BF_2|f*>gk7-"
    "=sQU&YjRSWpfZ|Ux#78j8033j`$g8oh*J%?ny%LO!iEiUtj)`9!0AoO)Mw&r%p~%bdk6ugrx*sJnRz$neW%mGG)E{4HnfvA0lZ;G"
    "5E_*Lw==!KesjtAd~mC9ZYn^ICy=RngCcalBueUs(=zdNwcqbBNo-i0H`Z@P^T$_#gQJE0eJB~%9Y+*X#X<VoxnA}|imIe&gAg{w"
    "!F91#Nl<R#;Eoz(;|%$3ab39=F;yy5heml<+S3!To&=Od6Jt*ED2g@r2IiyFoWOU@XeP3HuuTyxt&P;{m4`iiKs4MjJWT0re;Qg4"
    "t{U)}3m4ihx1kzK0ZzEmg~sg~{C6%XlLP0ov*0Hc93;md{-nZshJD!bX6i3T^=SaK6I39RBSJ!EoI9eU{RatHN4h~$XN2hN+`w<&"
    ";7{t}Xh=K^eJBcKJPfQ{oziU!I~!80W!w(s&XdP?&093|c&|w<%39a0E1z)GJ9Xh)f^9B)ru}k!Lnh_x|B?5e+s-0cw&=5{WQI&>"
    "3_#c`3-aFEAM)ONi}dW56#)oo@65{Vs_s7bp6^HI76d^M1S^)EQ}c!jMsMib*H5-P2XioTeY!HK<M?I1xC7irx$@ZJV-J&P%G#|T"
    "{NYi3Lv2Q4(b&f)l+Jgh8Zq7<Mwj&7bS<t3I#R$9W5mP=HFkqISM86r(4t4HJmJGvnKth_KPpRc><?8m70rg)IY7z8!8E$p{G}ij"
    "Os~Ru|30Db@4PXrJ+FRZ?!4<v$p1pAc>XiMF#E1=!CTkgt~LLxbotX-^ADsR4lRQ}s@m3(dIVeyj=b7xF}TtjwVsaSYAh%EiPyv9"
    "3rPO+3S;yq+K&HpkPG|=ZjY8AiqdQ7SbZ6onSl}2t5~0<`BYi=uC)}fhh)Uu?rix#Kz#7kG`bo>QTRU(vvTL#dLj*0nVERwmt+1D"
    "!iPdtVjM1+r<kTI5q1&S^x&+`7`7aXVh`<yEqWNq+flAnxNly2TIa?mqK_6FG=Rhqz2VH)Jq#QrRJTKgM_n~8#^mG|B>IKgsoZXu"
    "Sd0>7f)T3=6?Yv6VSHMK#injWQRKJsj3Jbz^Td!0VR}t$_zF~euIK~OKn0k|Hjq-kRBUa+K>mmJ@AhJI86*}plzo>I^?RuBR=w3e"
    "*p>P00H<rd(SYFdz!{s=Unu`FzyeVo9Tte9G*}?k01L$bgaslslqQhPDDaaNq+Ue!9Oa0jR6*+0L2!JWxU<TM421oJ8ql&&NzOD("
    "y3b**r$*WJe+WP4m##8i9YF{!76#G&{=**K2Rxw9dH()iI;4<*fhf2)&<?6$Mo=66WydtoMS=|qmP}$kQ8O5`w%Id0MK#5czR*(P"
    "<1Lm6O2a^SplT3(TD)cEHHnvFtt;>j6no!aV{B$!{P;qFh#lPC%8I`vV5u7F_bP#-3)tb<^Jd5#)SzL4EzWSwGXM)By7KQ%IrnAr"
    "<3_7s4(0qS0=S(gy2Ik&eWTqipIH+0RhSlT(~+vG<!V4+>X}9!&!?mC=HuucszMmCf9kMSUYXh@uJ-6IJTz=rmJhTV>W!PtheuyR"
    ")}NfS<Bu}Mq#>EeQ?ch0k4G{3m{~@b3E^oxyYEL+Ow-`UyeeB9l-_5}7gwyvPS|Op(Tm+}D7nwK3iyWaLP*zmo!0T{DDBIdHgd%a"
    "5%Cb7i94WYv|&y-vavtewTMO1r43h@w|3W~2I>QJdaHmRlrAw7^VDq-p=2F;=~rB`$jq+2LF@@A83a;Qxz9rUQ1Lu;uLh%Z0L=4A"
    "WZE09G^$KKGyRuS_nuu1Zixa{4D(OQqkaWcG87ubFBVi-376D0C@5tm-r`x%=cO=KsHEaVQf(B1Imy}0HK14uS0oU#A!&3{6;FEO"
    "nH-9Nwqj9i#tu}b=ok(<Sd~w&n${Mi*fr&7ph7Dj3j2PJDb7t|?*o%!Dh*qR4qJbk3*6F=ZyD)_GHkCdYCr&#Pjz&}y!57XBTekb"
    "&Yfw8tW%ebY`@}Z(`)B(I5~%Xgrv5Cne}0&C&XeOLTNfrgh!|+Zun%$<3RZji`1rWDI+R5HOFFIs(R+DMM$QTS^xf=IdAkn*N@_M"
    "8o>0<wo@=>OdBZ_8i*!$H4i_5yDRjNN!f<Are;HEk5r1nt#y>_9!7cXmR=4c_9&NVn@2@fH;=^4)Y70A;}d5qP0TV$&r5@hg7hp9"
    "f^YkTVB3X8x?OAdYAOjAmVq-JvOzo=1@{|BZ9~0Jps?06-{<$jqVJLQJ+c9I%(?SJl>(n_ZX;d3k0T>3w~p05j?!06a&__;vlcNz"
    "BlM0GO^tAo9&iOdo~O<Ev46EI6m55A<lL|?0VK=`TduiPfh8o9P5Hd*X%o&O187ui&4Lk+!O?cy(>bFqv+dQ^vL_IdFSrVjn8R+b"
    "Q^A#vPMPLwE@vH^4Tj$Q60{j^1go%>d>;!$hIC#|wh*F#qWR?3qk-3#jI!eTR*1>bb6SJA;#BSjy!(a5aw<T0T=J0Lt3T};%$1@n"
    "LsL$Zt96(1U__CKh}V8FW)6v=fp=cRKn=M?rAOrG+}s+dnUPymS!8sk3EQv}W#T`cQaS;66v!Lm!l4L4P{dPmY963EW;ZqJZS^K1"
    "0$0#_>Dvj$7dYT5O1Keh>oq`xs)Fd)DhBDHf-t1PCl}O*tKnp!!W7u`;bExcAZW$)z~N1$9$55(9fI7f2sJm4F$LvJ!v~nTN5ArN"
    "Bk;L`Gk-e^t5SS_hI=5&3t_MBdIu5J3?T<|MdfWeh;yxu2puEydOPG&KVZxxrN5Bz9`F02u}oy2Iz9kb)yMpP4h@0}d1x3T2_}eJ"
    "i`lT~^`CTac3b10y>)SwH<ONRc68@T*0iabBRr!ZuC;v33MNDn69C^_sGMiY%Dz>zN7b|OQz>r>nbMi5#hSIWTgi-}XCa$d{`oL;"
    "KraC)@t}>q4P3S*Lb-n1aAB(G@O*vUm*_3@c}!V7nqPwWOI<P2_3JZplvvZJxg$*$+jQ-tot}~W-!rP;y3%mMK<y-X#7goHB1v_h"
    "GW(K1UWzgOCrAj9B=TkPYz^G<il&h|ts1;LsB9HXSN4|Ldz*$HhCmHSNP_Snr^yi21O|WmOG6NYH>M1M0k#^H15vNEml2s`cx4=`"
    "10IZqCB~zbDZn0~zFoGnu^<LLH2neZI)(foJDnS3sd`z#qvxDxunbvlukP%gVq9bS^#t<|aw360i%RK;sPXQraLntPuByZ&s}W6|"
    "@k(6`x<F8ufJ`1&AaO~ju6vSi1wMJ0h^p=xy<4=+kh?4(tGlhe8A8)Y5tW6u8TOXbcJJlPN2*w(t&Jx^1}&kEtIW{^Ph@@iDtqOI"
    "xe(-wiY|7rM#6@;pqz4lChoS8!69Ln>5W~HJ)016jskFjXfi98mhjU6Iis9Nu7UDSKw_tga!rx53Ubu*gyi-X<g}@s`D%iCfkf9O"
    ";vtk1@i0UNpE5?Uh8uwf-|+{!qLWGnVt`3`-y>(GGF)ES#rK}8qFp!NdhHAOZ|Z|p9vjWwu#6GV`b+n~!Z<sG&7{sBiRX_}q5YKk"
    "BhTH)2tia}G$+8v(!8;N_4I~E26P<ABsPya>x98Wt7iec;h<2)hyg4Lr8lS@=-DR!V;umcpV5vAML*<@n9G}&5knK4u1Oh|nyPlw"
    "t+UzL9Q&g-MmY75hedx0!AgdDOpG0;PA@sLOxdZ9O#%f)Y)gW9Tg0^W;DUg9YV}i#_~SD<6^UxLBU7;|TNSMnP6ohRB<M=-63ivh"
    "q0NQpLy4WLqDh9T2wy<`Nd-|Mz+TP#riHSygr1tJSKm05pKGl;5wkEGyicnyvHg|)`*`R;Z=YW!m2+3@_Dq1XUk)qg?SEDAXJcu<"
    ">MqufRTJ`yS$O(pzc8v@Ek-JG#0NK*bckRi+;~!14;3u~{<sQ)`lw>4#7j<W;h8x93jjz+)!@r|OR85^Zz5--X$>^hvf2QHmDxU)"
    "vziG;S-?UOl7`%RSS^oNpk%Kt>vIopH<_T2c<u);c<cQ{Bj>^#GECLD>$y^=W}fxsqVu#VZYh=2uaf>%s=+cST6FI|c3okU69prX"
    "h>ljK7h@ABEy)HBZN16qv41{#?<UkN+TG^cQSVf3Lfh7IRPwF#CY$c7BFjW{ciEyQD1E<@Ax~$u2|b@+Yg2F1Hj86afwfheXmE;e"
    "Ah<UQjyml_!T!}m|F*ZE4^6yp^s|W$WA{0K0K#QhwY{S7QPU5gRKGUahmFP!H1XwbQT-Ts{jEvoDdjWn<-yfdo4g@3!W8v&qxm7v"
    "#@3<dsLY3L2~<BCF*q8}bJqbGq}matqp7r?O(@1UPA(&N&NbwrM$k?tOEJ&seWT$#!x*azBB%I*s9)PLCp#}PR&xqi3JD!O@8|l9"
    "C~LddIhAsL1eisP?+XpC0pY$OA*FQ>#hD1<=d~;h{o9oF#*r9U5z=(E>8peNkT<yPfy+I7u;z!uPI&<3lCZdNeG9V1%*-63KL*&H"
    ";EbCf@Zn<E_b`LYS?nQtMQnwm%86JyituUDn&}`V87U)ih9;3l4Zba@5MInz;D8e$Qou9s8<`*HbS>_wZ&mMdVu?v&qeGkDwf5Wl"
    "CQU2he$3yOD3D2}*ZGQbd^LHTxo25><r}Z=SHwCQ`g#n04@gUwlZCC0(~)z+Bd}i+>wUCa8cH<RA41YvU2g$?XURu9Z5x%VH`Ve>"
    "m;gm94FR_}QF(U?As8E|qAv|R`vp8!&vzjXDlsS+%V4RyS*E=gEqn}2N4cGAYxHpOzpcM=<JQQ9EdG)8hyq?suwPZLXe#7-5$Wqa"
    "_nyD|EuBMJ-I0|%Rao~z0c}<x=`eK@-SbdUKnIc?BsDnw_#hVRfGR7C-I@ndCeFZmoHG^z++v`VnlumXHiy(*8S+t7l`_lttx~#`"
    "EVaF@Q?9byWL_OUv^;6s6A5KyVj0;s0Fi1T;=ZU?mf}HK8H*)EyIUc&igQ9SRx>yq+EQd8AP{f$MhzN19NBHoU-FNDHB<?z^C$c^"
    "fAPe%H+SsJL%xi_8%wst#f=x7yJ3#dNUZC^S6NRJV5!|N&Yn$v&7f=;m<`XAF(uZp^ejPFgvntZAA+PHvqZSuZ>eeqq6RC(OD}Wl"
    "oC}Jf51y<g32ZUqK-f=41|U&cjHg@5h9UbAAFyh<lX1ya=SrulV41~L#A21M745%<B?UN@^Lss%V`n|Sxr-jp8)e{wvK65x>RR3I"
    "!?`1MK|vf5RAXdwKhFo-?9L=<b^iVz)z}hL<P}iibKB+d9FZgaq+(}nEXddj{5dioLInT10(aHZkP-zHU1ae)!p$2swePQ=f9W6g"
    "i~P72@O)({SieA4V}!_Cn)hZy@>%4>DN}FW`Z+UUz*U4t=Z&}wM#Sw(MT#20fabN`>s>hPITl3xX@EjoB<Trz#6sG$3)cuHKf^ic"
    "p;L4ZrWuLd{Ov~}*fn|vwvsW*1nlL?!1w07Fes?)n8qG+4+Sr)o9-<a{0NRwX<VPBGX<wr9aS?`d5=nK?As|{fGhOl0S5^ks1aG*"
    "BuoWxZT;{@Y=6XOQ;IG4?bt9>S^vq4yZ)7~e({m$=#C$6ZG3EVksmkMOF1JdCB2&BQ0?m;)Akl}L^#a}LYeQzszArWb=*s=U3S8b"
    "A_ew+m#pa`6j6nQ$g8py3h!OPGg$5m<@aO9)5kVox=6T5bUzE8a97rBI2a)t?lE#Z-xi73<UJ~TDO?R3)GmoCIt=0c6BUnrPN5DL"
    ">A{i@Q*odVPR=DHx!JJTw(r@qbj+eb;~cO3FIOZUVPJ(y+Rh6^;JIB{)mNZuMh+jmFb)xkD=!YDcq?65&W<;Gl`!TYIZ*|xBCXDf"
    "xL@A!=ZgT%m7OQ}uT}#}QP6!?D6plwt@21r>V{xmh4y;GP*V8$DH5u<b!J<^e6O_0wVf7ji4VMqqd^gIx(3dwR#O^@bp7^tjO=<("
    "WyN^YFj=7b#qL|iwSrLxvsP8Q=5B1NRhNb^WWzjqIZ?<l;BVX6aBp>uT+$KyJr}0Rrt_R5c8DG=Jl%C5saZJ5G$ARkt2A86S-Y|-"
    "QwNeOcT+pa0Ni<roZZ|i=RK7=K{}-<%1;A&1z?E_<;&)NtA;a3fuw>E8YwC#Jx&#wzAV%GbLO^I3ljjPLb(yysh_7!l-S4&i?^5h"
    "nJ70JIY*sW*lT`3QPL*XagHfY*?Oboct|aj8RG2g`Y>@jg`|1kDW^+apnG?-*yEhGxPk;-VXEz8xWDe^pCxQOQi+(y`>sDWRw9#w"
    "f}F6mH1m~k*C9I=Tj2?r<MW%8#l*7HF}0VIQ=5)S>raE3s{*JblS|GRZs`pR{<OGkFAweT_!CnTdk0D0Xk2m@u=%8~rFd4A4HfP{"
    "{TCO`Sl5SH(2Il9npX`KAn6<Sd1#j{>%0(ooM%~0-(=H@PO*AL)!>EtF9|;HHgDZ2vM;qBsA+@J?2wfcsbC#VH)0Zo`9p3EMVvF&"
    "z}xmm*&C13GgLw~?`j?_s(FTlP-T!v(L>t^36zz4qj_e_c~tBtqmb<|HdBZB8GyH>D1YtIkr`(h$DC)cgZp4U#KJWQF+4w<C_)b)"
    "Dy6Nt!l>VW)-6qCk<;NmdF+S78k+|DFNJ*WbI<xg3IOjTw>%h_0pLI0$F)?)`CwEtM8Pe`*aHb63rIig%VckqR-42x%Cgxvd>_3?"
    "p~7vuF;0m%J$~QlGC5fSYA=ivtRXS_z7dYZ#Yg?1mYar>j-`#UNiX1#Q$z49LKE^~MpBLZx{>TTJ;ufv&$2arUgS_?9iOO+I*b#S"
    "k=$qAi`w&iS%@}ITLM$-^#LiPtEZtqV5M8G;uixxOQV<YqV4F?kh-y8F*IkJjF=xk<&>kZ?t22k;!sUyUgI^}mFdb_#iJf%t%NHm"
    "I{rQc6jO5*ZCDlcl{aRD*46X*-4)7hMq#;ktNwQLGK`83yhyy+r7zADdEmG)B=x6O^9W%zK46qeHSRXzjZ}$+5M7+JY`awpwr4!W"
    "=m4eyUX-kHQ6`2{t9anC6#860Rs?DB{T_j=R(<{VRH(PTlsxFo8<qssm#nCK$8Zdl8Gt2ZJVsFH{V*TLNU$5E{^v3HilyD>vChwS"
    ")bvMx6pA!{+?QGuoyPIqBmUmj4rM&rbNu$ahIvu!?}&P=xLQ~T(fU-E$<ZHf_|L1WDAU-WyX5>OkKulaQ_^Fo^w3|6_K2W1KnHyG"
    "p(l%eh!f_Pzki6fxaVU8qUZMx-pQu~b@{hOkek<SUx|)ivx@O5V}_}sew(Vl@bf*Wzwq-t1%Kh^-|G24^HYa|{h1g?)%t~V&=I(%"
    "uZ2t*b3;_-uekF)sfgr3WlYg0A3Up=r!dp^AE{8ZLOZ18G{%UrmMo`Jx-stITZCu}$8g@kpNp_xMct=J)E%R-^Dz}tMW-GrCZ{dM"
    "EZKE-MssOl!+SLXe1dz}P?SOy*>xHVOvEZ3>s3O?4!JaYiVh!fBv)mGzxA~Rs1yaBBl%(MaabGky!as9Zq-TY*mBMtc>WW=OG-_O"
    "sr&!`*s;&==<gl--x~8@IHrN(;)!P7^W4ivSVHD&EaVEZ7=8IaeWLZ!&~gPp%Z1Q7r7@uy25S&<1_5c5jsNS7al{eq$q?GCahSkk"
    "d$v={*dZ-vhxYcHlTwX^Zmb;$GMk)*Wig^kowPw|<-S)vx%PnL{<1QRg<K<2wad~lDsnAA{nl||co^~$o5QjB`>}dtlY^Sv<IJ#`"
    "h)ga3d-Bw{qo7#9emD8pmr!!&Zv3@5fiSp(!7wy*iZK)Xm#DGR9S7-h(iODm!F!}N=dc%+)7FJ#d;yjgasga0F^>ND^&x+V%IQ;I"
    "FuoMe8bLgqrA)-kzu#ru)-uQB^dR-2mw0wD<eU}TIs!2BLu>d~TkgNTXaDba@VB*wEcS~~@1#lG3?;+ixJ0F+^tAJ+jONr7Wi@K}"
    "mx;1Ub*^Tgupt}}Fy}h*3pr#^7AttykTzLF-2<ox(mFx2ZFjWpMSyzl93cAjlB1IQp?1Gq+)!RA6jXK)$RX~Y?9|6{taaZgGq)bU"
    "yN}z_+0>(V8?oK1cbL(-7j{JERILNtVH;61tKBa`J498b+@oeKl?39YcJI60g5zMy?&Oz_nW6jJdY(lvvY0gU-916(nu?eRGGE;r"
    "a&SMof1h}Lbgv_-;qFNt1NrAx`ndMzDueoa`-(m2==U*|H|+BmA_V+8b`bnu#~`xHD?^t$?_&+#<c%v&<1w_0w>#&(lMi^thGUjT"
    "k(SvLauaCBZpYYIQJ2KM@z~}N0+hXk@z{C}Nf@Q`$FXTZi;5VI?Eso~{dJ7#-_FF>F_bs@eT>XeK7A|A8xn~Pjv&#xzIMCiWU5f^"
    "h%P}brSMMPO7s?Xj59$@+)3lNw+}kBNPL($w;7SE_hZ$EoauU^JSB2*Wer=Apj?5Mr?Z;Jy9n^T_oh%+dfEDq+h~QdJM%RxuXEC4"
    "@0LloT{b{o5@fWF{5V*B)G2>46+Al+jel#50$A^C4z*{;3S2^LQyT_|6lEBEr5{hoF@A;|Ukem+U3o_mE*CxL5+<@{@3U<=ONZmi"
    "Y;-dpv(drj9h9(XTizuHZ`KltCmuxico@|xE2~E`!a;MtI)daNFGhbjf--Yy{U!3+wnL?>`e*J7SU}><AXZVFG&!-0x_`!sHWgzN"
    "hdpm-qV;nBaU*l<VH}IOvNsI3b)5NrO8lQ9{y)@2N1c8zYTW^@E$Tw05{xG!zbxvbni|=#CO%%Hj1rI6--|k%t)_X3Bx7HTdOeAx"
    "_@9gV5coTby7PAy_3M;&ENR=E==P00Usn((^%OrA_1w?DVxu%79)2%s#s0bBMSZA~OFv%JnY&&2_IG08V>W!2Ul#T5T^KG}N6R*v"
    "h@kr<bDx&p6MWTqty=yaFFGawAvW?I1c~%RBRMh|gmf%y{uf`=K??e&w`T1ZU(^XzczruBf!sv%;fN1Q&X%Y=2q9_kJLQHsllSqg"
    ")Ki9IwvF3|%CPloyQtI+AuD{|mqCwcJT^);esL(&jqA8uL;<B|@-PWs^!wr@2Nbq^j|KR1S($QG?(bvdYP-10(O1i;FNPgs<-L{@"
    "O`~2O3b3dS*!caRyt4hB)v>s_ujGM9^kQ3Aj^1Eu(t^mAAFy!inrR%V;<O2af6AT(3!PNdfOY<MnUKXXa>s)JMh<}8D&e!<KC@b|"
    "?_LgDyGva?jHsQ)ONCPDvF4Sf$Li&r(hbqv5S&@oGc5@{8Os;nSRX^jhX<B~Em4}sb~3BNp^DUzmy?Gp+g%2a6)G#wYzQG7;x7ie"
    "Pnmkq#-xQ@CRik>s5NQ{JmzxHd^a^z2~@!jD&pr#HKdqc|LQSS`W^0F4DDp73j4qMm<~a%s*21H`v-`Ja+^fmU|*oBC&^Z>zqb;E"
    "Q?poAhjq=!Kqxlq%lMz{iYvS;rjTTr%9QnqxbC5=1CkgJ@pMAsPEW0CUXBkKs$=d=cwl=O`Gb)H{ke)DKzA}!uRg-#7KF4tq5ZyT"
    "sszouO-Y;7+K=!cNX)PyW`V<2B;YCU509@Hml_b8h@>$f7ABG1s_h4f@C8NB)KD8yMY7+bh1x<Xpwl=YjwvEOe>ibmP6IB6&|=!J"
    "2l3R1-#I~7P^Nq^mR$Js@L*E~mDE#%Q7kce5A0DUl@?1RQfSkPt~bl0A@GQ!l<Sb~GfIg=ntuOtd^LtN{~-SP2f<Q3vT7H2<2wHi"
    "!|KTF3@-V^D;@OtZP3{pxm5;~y$6@^A!p{yBh(c;ba6#q6-<MG8B2imO{NdPP;n4Zk`0Zm4Ca>g5ac+ZoS2(aW68Oi>?@tk1Bi(C"
    "7&wBU7H$kS!(|+HT(kisyVgMM?$)w-L`bIV!CoL#mHCq>nXNR5M>*;Yquelrxr^u=DjD*u=tc{A3#PA&40T@*nTV`=M64FO$l=~S"
    "4kYG##o{Rl1j|t;RL`vpLw+JW4}i^~2riiN-OQz!VjXW2sA>mM;=GvS!%8-I@3<ystAm$bC8lUdqvcwrn~x?UDOJpYGzZWcR(R9{"
    ")Wj-_YqNC7nOo3F#Da4(5J@@O=2Hoke?-+hHMDg>CIQN?)+^%?n3+y6SbBTXG&z=6J=O>*Jr{H%>(Hz3csS17^<-p7sdb>h*7Kc}"
    "*?XMh6~*M1k>-wdRTWD`2b%x*e7RbJqGXYaAkP^CZ3ma=J%MUHACMBcMyQ5z#ub#*uVps^uv-(jGDNJavG>a93H5MW)WJDn@uO9X"
    "vSl9eB{di1%<jk<qoKRt9McxR%dgl;5vQBziU6Tj$0GZo*{6)3g4>L;Slge8OxmtIh~EuK(69L&pK#sFymq3S1e$~h@-dl>)D{Qn"
    "$}C<kO6etwPb42($Uf;cgXnF$Yi!*@kaQLDHccS;2Jj7wkWoe=we!M+`D>iuJbMcwSWa!zrOP{08|W7AUc#wk;Bx?Tp}!TJsGn>)"
    "$0{IE;W?M3Ot*;=`k~NL*$E2eCXgv9_98QYq&5rCNstA!yixKmZ3~{ga?BJ83k6>!CWp;!r&b9WCQ1+I1PXV<KJBf96l-l?z?DJ;"
    "#-DAg?{?|b5+EeEtk08{@vv`_A2oD!oJ9`&EruOhD99<r#CJbG6?p_eCJw)qdw{5vg@t4IztdQU<NwGR02KI-^54~=@B@m0nSCEK"
    "OoS-i1>pU7WBqKAquqNd_SH;7syq$?&)gdpf(9%o#l9O@G+mhC(ULV8kRy=JpCCJ0o*ijLPUbTJBjnWg^6+})tYfTe&l2`XpwP3L"
    "Nf&{N0Dwi&y1@=kGvSf6Vr_on{CdDW>3exURf^7c{YGx%*O31|ihnV2ACz<a;a{*DH2;tL>kr4QlL{D1ES=`a?Ps|nMW1EQ&}#px"
    "Z3Lx8uP1sJLK0lNWob5kR84vc+~d{lH@`|OiFB@~ML7)hm_${_+%gt#67*!;VW)QTtI|{1fn3vf?yXi93fkDRtkD#FywP5XdZGe}"
    "?QegnR51UC{q^T#))^3VV?yKaRy3XQMc+IzR47it7yP6;`K&9t2l{QZE_F<bO4VLaHP7uS3*}RvU?+i<@6w1&2~UGL$O1X!+Wf$$"
    "eeT&|L*^YCK>{i&r%-ysH${Rt{ragfC8#8}9FzvPD)Ks_29b(K?1!o*j*FX$juC%8b=m}0135#f-X7_)c3rtq(%M=tdl(r^uV++D"
    "?cGNPT8$7)u~6ntc702vAm@yUpJOSt<!__Wy()<++*qva`6#;D?vQ=t6!WtkB4>$qm;oC=;JgrL30()(I4_GP(K8-O=cyd0yseK8"
    "Ha2vHB2KSJX^s-~Nh)*?Vi}WWUL~D?fi((xK$VKCfTNm{{!wy<MR)uSR;o%%XCkgcnX2Cm?#gXtLt@_%eRl=Gq9}{Vsdi<2aS_~A"
    "ZeQNh>7gJY<WJNU1_AQ8`-+LUaO2<>)-<x+#7t&0NyzwpV7m)x)XipRp;&_RLtIN{5_#Meg2V8bYPEM){_;@FBj=5`#Db!0992wx"
    "z*cFl)@8DiS9?GQ7wY@Tl(u^gG;%sY<Nty)_FcIx#T`e7mmx^o;tdF!Clgko^!|y;k>nVev<t1|XpVNkcReS{^DMq>L0ngabRtzd"
    "|9KW)+v;|b??NXz8VcKZ>u9?Dy6@MhPy))XB2_Yur}*M@&WPWNFOh7AN^c;V`Cu9nw|}V#8Oi#WNw<$F7I?GL<dg~xybHkQcp*i3"
    "OH191u?SN1FJNtVlWf@1N11S2n4=`ZA4O;sve<SPHDOMMP!nX&VV7*Q6FewQ{3X3f@ZAf-&!dtRmqoeJ8g!CwoN=YN1s=<AG;tZn"
    ";yPt9shB=orMpzo??2KZ?TK_Q3RSM?)YPneOdni5`_o}X3QQWSJg62Vd5P`F`EK<l+YUq~eG1HDy2{$w;~Bp6C|c`i%yfi!gdVRZ"
    "@bv<KjI!#(h?+vhU((0S*M`#P3Ll_ez(wvgdY|`Y7k7_eBIPl$$&ho`%^+qVD%id=o3Q5o!}Xq?(7xNHYrbSEM)TFY#%zJGO!eXe"
    "<SST30z?YOM@dIQbrC>Rw8=Qqcn<VX>m4!X7%END$5`Ds7Hd)ei38MEohw@_p3z}<P&$<gF+>okQ`NBe&tIl9XT0A$Vn`slq(2q3"
    "`t>y*4?2@&$9oZZoGrrgvF4{BmB<1c_T8^|wJP6sVq>eDeUz_Na%pS6^Z0emBRHX7K8qW_cg69V_Z2fv<wkv=tn0=YSHFMweJrk1"
    "0%!Ou!$qG3@Y;%Lyyh#72xly2C1$YC2~R>i5WKWb*_vpvh3r<-hs6NsN2oqaT}~n7d*cf2q9ffc4crq{Q=(IJe2Ai-8`qCb>aRC("
    "Hv=K@l<H|sOd41GI<UnX$lGIB2`o@*fVcD<$!J0oxCtK#6tR;|bR*$~ger-)ArorSt+-YXB0}zaa#-X$+E~aIvdRs^1?I&6R1-nt"
    "0^!m08MpoZo@JCx91uaYS^0V5&Y(^Fzj~sj5r**C>gTj%G3{OGn#3Q!t{+YOjHaXfXPO*9@@?JNlbkMf{QyenzO>9@A31(7hI@QG"
    "Q8qBHM^FKuPBp^(_i9s0SL{`YndI1<Y-nBWQI$7Cw%h3}>Wa3A?u8u9FqGDn87d9L5GV{D)KzC+bw}l}Ecvui;eEiW@gC}m*=FW6"
    "j4GEX+1}7-cvO=^SP@z4`PlG)yw~2vFkSBll=x~AA(j~)5INX#Y1hLrSEx=R+fHe`CV#$C|IG#Y=PMP+PbjR+QCOKnHD~RXx7_Mf"
    "bEzOfWZL&m_3DpmHD{)y=Cf<7k}Ts+roZ4!Rs9Ac%f+Ar72e-c-O?C|5_jIJY|v0B6Tp{&<|{k``6`mCWIHN7AJ4!J1r|Ur%%E(M"
    "xt291w9sYXi0Gh%qsKE{OyYzwB09Wj%guvSy|8{+PklCc2k0`y0rkIeSwv@J`OugCJ@H(#`~J0fp8TI6o;SZ~iX3@LI7>5EX!u07"
    "K<>>XAx9>AMRBS=2Ja`|NcJqO>28L#dB;VRpN5dLRtZ<oiW1>uDN}<;+0myxxfDm5V!V-UZt>@ukX>=T2}-exn<~Cl4j1TWmid}2"
    "#R1=G-%YW@ULu2TM8$#$Lw(Ygzxtvmp+Ft3GXNq+WKQ1YcI8e5vw2lh+8Ul5xrG1mf1?@s?{5-+w%_QiHQyR3*evsBP}fK^UuMk@"
    "%g4V9eOY119Qd%p3?|keSz!i^^uN~%`>$E2|FVfjkAs|nf`(SFz6>v?7_-&@suB0YS7VkvmzlwboOKUOl=5``0-|@sD@${j;bn~&"
    "fV4#r=>GQpKVSXlTmM))e|DM9xAW<~pyIR?blA%Be&pKsgnTWk6@cu>qOpoj`3YY+pDcTXektzC0ao9j^Cn6iCW4)woK1~VJx@Au"
    "qlP25mK-yB9F)P$gZs9lA$<h?P+UjcEyjU*fn%2^q=TKHTr}{87B~LfCTKc$C?<V5W*9zE%L${g_8=l57QG?l$YfihVs?05I^dy*"
    "anv!^;XN*5XUYd$M#~rsSy$$UMF_jI;W7<8^!3JA{3~};E<^e5TEvfWE4#+V#uyP~VQYJt3U$7`-s7N?m`^n7(drmcKnZo70O(^I"
    "LAg7SL$^TTTba+hIyi8xRt1VB)Wl&+D{Iu)1mQ~>o8V+oW0U^iy9tWE#*dUsX#%Aan8boYrOl<tq%jzWhRnss)kprQ%;zeQYbUOm"
    "Sv*MLG!Wo!F}f|XkC5uu-1T~DrU+@dghXrqLRkiNx6(wX7J{?@LBoAOAVQFIam3JHxpn69D4v}MtnY4*smp_+rYLa`MVC;Gq@c#s"
    "H!Yi*u(*_EMd7}=<V?fvB-g8$D=;5rUD!833klPkUmOvt?U?&hkyDEkF4=$#l`PAhc?QK(V8W1l<E3XEAP_fEt1TA<W8D};oX*O9"
    "R1f@xLw2>xAfnp7>_txZxr>pwh$7KUP*^UpyxSi~h<Yd~AE7X!+=yZ|O(`}-@0`S2e{`rUxop8Uc$}y_N-Jrri*cX16XcDFpeg}W"
    "2Q#Y@C#>yCtLe0ev5(2kLjnX0C=<!nW%d*@tGy5u)PZ;CN`~CikK&=?0=UNl3g#nR;&i{*o6wf>Gwew$4jxP}j~-Y!R30{OBO*a@"
    "xkt+a>H$_#wkC&({#E&FI@EL)HTwvG*dnNO$Xw-(@F@qOggLN`=oY|#evnW>9o}USat{guqWIp9IYmR&d4UyV&&sV9yIp^*I&t0Z"
    "C%R3OYeMjk&QnfZx_1bQGPe1mU<OS6D}poF-3s;g$hiW>CLk$-!MV@EVTqF3?~Eg#MTs%6VxgM4|IT$))hq*W6!AcL9v2Pr9DG#|"
    "5q)$g{W4Uw151iktviNfhjNAoWX63GbtQllm=+poxAI+XE1a4Qxv?rnPqW-WAoJ+ud*zqtRgC3kS<bElI!V)eCKUAokUSSd?*d@+"
    "nXwayjYmLFzeL|3nWZ}RcAqnQbo54)RNz;EMmBC(dO0(q(87$3*_F%^TVL(wVrIe$u-ns6)s0}1aA=2)9P3X@do-ryT+)_%Cm%%3"
    ")k_pG2T&|<2r6&ZD5nWZ6*?GuS;b$+Kx>%TT;-QdB12|jOw9#rA;}G!Unq3VhFHmJCF>$&CD}Ox8ZRy`1^P9^PH~VnSTWVM3*POM"
    "-k9V%NtDO9S)T%ZE30pd-aq}R3Jx-SQDo`1jw7R_JGDs4@v95Dqp8CoNxrOEvA@88w92SvDlR=80M0r>l}5;X$#5229R|hp$)G=V"
    "!Y)w*I2R1#BSik=r%pAc7c;*J6-a-)0rflBwMfN#7~m7fX;EbB{S(3A9S?K~r=daCxbF>2fE0#UugKwyHc08}g2Y~GJYKDu$_0?}"
    "+z<d9@<78el%t4q%GIA6{$~7n5H&c0lz^tJ<4MLD9Mpt-^xm6c1IRz+_kF)cg~#l@Brw1aMqWG6c|5CtfK9!h_iHwkxk|O5(5kP|"
    "TtSvNklIkN3z)Bo<Nxe`bXKg7_X<;1@!QU?p>YQH^7&&z-_Tkk1c>4IEO$7+f1)fb1FMO*O!wbh1_-h4t&f85+<O~Y8u&AhaZy{v"
    "FoRq*x_bXiwbRMd`{$n8jXNgp9PPfh8DME&yzh%v3?7xDEgAA|031qB$L=HdkNxv`!=JNp(tlP0f)IU!*1U8yF6tvZZ~Rvh2<v1w"
    "b^E9dR;s08*QwEpG<YBFoea;8qGcBOM0Xi3){$7&le_p;&sEw+=Crh$%gOF&9S@3x`ef|-B|yke0@rToTr-2pH&Nw3cJX7Y#1NXo"
    "wg_-0%Bgm6B;H;F1Zm@Vr?slMrkgqac*VPVk;^cw`Iof3j##)J#$F|qH(~_+6mA-pg`UQK&)t4B`Ps`~xDjHZHn^ak-3a?xikbh>"
    "#Q#YY_J%B@|DzD}|0Yt~e*!oD6XW#{(CmMX3X?zT<YVfJ|JR7`Iu9921cAL0c%S}Z@SS;%E*<<;a2QXlK8VQ>dKhq1kzXBr{>Pl2"
    "-FCm7kP}7!?<dp(Po269C)=?9L?4jHl9mYv;coMz{TO{1tArmi6_=Kvx?9xj0|d>WZ5|&?W*GbecZPy%>`NSAXO#963ZQ~L#JD~5"
    "E)x!vec9+myk?z`Pa`;E5S^ibu>MJL-|FVgQ)OlBYIPM!H@nb~<cO1w9xhTSYX#?C_N5bMbnDV`L=7hk<e=$kq=be&zcMX9S<qND"
    "J(T@OIY>p%&ONoUpU-nujiFy|J-c5_sPeqtuDuO+oRg%ei_3N}VzNh0_G?44z@%5!d6>CDu%M~}NK}?QpR3xK0SQG$ai&{XzmI`;"
    "RgsLInzEes<_}y-eC)%0_u*5(=^MuW_7+{hfUR_p>gr}fp3z=_trFXV+n6Jjixn#q$aMOAUPUpB+>&4O0*SCD6H#z^9Y-eG{$yc8"
    "pO)vJ=vDvMp&eCrw$XkzhOb9uX9Eotv$N3#b~gGaI~%65M_=nds7!oMhf0D&7|x5-gGk<@ug!e*Y@(7;GR-8yuGCiNRl}De$*^6y"
    "_7$d*%FZ88&O0Wz6IvXs9G;`jnMR?;8o?^$gFOfflfVE4LeM?SxX3>2_oQPPSmo0nY-i#VlHM!K=-R{zNaM@~d#<`Wxkk7u7(({d"
    "GamvSZcT!EN)vSLGE>YyJ94>1&4;MEQZyPd_+AnJ2=@9@tX^;de>MI7bZ^rjZQa84Tu9YU=2%Cu5MnzI+fG$tP#i(hrphdV*wKkw"
    "CMCEnd3R?)q-~si<+u6mLD^H-`O^#0f}(+lp$R!|j5Jz^(cGiT%YP8uz#K)X4s5+#QWl~6ZjpTUw3SGdSzv(MD7Fpj$r4=ujx5ue"
    "KTx=vo6Xz-gC<gobUGbevWHPB^$1OXNNpH6FZnp-t$SnsN8JRAH9AP#x~Bk<Acu&+t+~i`ddi;9tdVD=<rLh9o7W<ke8_!#b2AB!"
    "VB2|NEIBm-DD91s>Ko0r^Px&8iWTOXec8UO!nbJx1w4So(2i?{l-Jr=$A~JHC3N%Vac*oI$O_-ki$!~Nb8PuGc}bRXCl`PcrnZCh"
    "WJ=^a2RqaQ)cwcGXfYmglOY`<H>pFZl%VUZ#aTG#2D7tb5o)wYG#Va-S7%V#p#Nx0M+|!RTExc_WeIWii1B1@+HY+FgUz`aw}fo;"
    "Iq`B&mnRARg^slpMRv`T(Pm4zq768X2~J}i0yA7i!uSW_js=w0M{z8YCc9Lx&?ETPc#YOI=*2iK*E8=6qGIkvpW2CP(_8emPuq|X"
    "ZzY2fON4OeA3R<#PDJMf>xEMlQ0j(K9cGs+)10}U&%z~~dhp~f8ZG(l<tsTZTG}?6a^4C+;&wB#@8En*#2AW&{pp$_HBe(VV}LjQ"
    "?F6`KROoe2cxm|ySA3k%IBh^8kt8NJB{*BxOT-q`KHkX|of=II_HMu%`v+7n#rT)TMgy;y#Bcc@+m`c0Jj!j2e1`carkx~l(gV3c"
    "{sc$TlFW-C>6jy=kRz`Q?hFC370cL6?KA|TvODi;mM62>UXEa$5UQk~(1cndd?$_ZML^y2>e{C|la5@hM+mm*u`wNAfg)15P7Lgt"
    "98vIRQ_826F3^*P6Z-2_Xy+{ee+?_|vqY*v#FZ;bS%ST1?947jk`T+Cck`xwLSsr1(5hzD`+DT8v>J<w+@s^>xLsaKNS>y))w2YZ"
    "tG9po^Mz9QZ5q4C$78Xz^*P9HT79B8D_!{z8E6oBqI)9ftfQf!#G2I%V!;u=s@3Ls25pFu``8}`xclcO8zYKNMQ?zFE~?k0{9~%C"
    "2Xs98V<7_We{g~IVB%OioCnkG)?#H(X#oB4&$<-Y#<`R~vq4o|_LOxAp8H+BJ&l?#NQ9e;=~PHLOE*KMvgK6?Fz)avDK(^iKB3WC"
    ";Aa%{jYu&ILlf-%ja3(Eyunb8{WFwaHEk9m*4Vi48s|*cx=@PdID#rp^Mr?|fGg9f@nWj*BW3l2KpfK07@5Nm5ccJ68aIUTfh&Qd"
    "kCSurX$nd#l=hySYJ>}c<*7|As&vI(xx4x~M;;d}S;jX6BuaKIzW5bLiG+%sQ6^PsQeEv{Cf1%C<}@CK&j%*6{g99;LbiXK>~~+O"
    "nIhCTX;e;CJBIovw|i3!yQk?*STX$s*`sKlX@abWifHdrc3I~Vq2Bg4fk?%abq1$IERZb|d};9VblDXQk>p*pC6*;hC5?>0_`u*3"
    "pFm+9F6x;s?SAl$<{T)rLWqerE;O?eLx7MbyJ{(7qL21nBID1P;!t&1$KF{o?JqM1;Qr5#bCWK0PWeZWh%D+a>U4a0h@|<h%rMu8"
    "5hD3qQm67pd2=3LSk72TFA*WO7EfVO^b&hzV^mgjqD1CKL>c~S63JzzOg+i)kRbijUFYcv<TSwh&-;!JbVqKPvP86TdeDdNMj-YD"
    "AP(TRW3G|iDE+ZbMKz#3b)Z5h5wVv^^e9$1OOWJs(B8RcJ|gB46)l-dJBgUTRp#eH`an?bBNe2V)u#p&53-TN41eX|x|j<l6Laj$"
    "gr6zprv~=UAews`*(kg>8YTEg&WOd#okPk!g#bw4ic5!Mr?9JmK-P#B@1`ypu?KqmND54nzAQnO>W6MH#wyCZr}S|7Vs7j*sK#vp"
    "8Ku-CExF!EZB_*~KEjdz$a!wwO}XO;`(?=6%p26v&ne8~O~5YxW5@aJA1csQO-zdpOl}<iK;$Y~#FJe2I%Sd7Du{_i%a$Np36=F-"
    "*%wxE!K{`*F|o7gBmABy-IWvOW9={uMJq*%qj%as=?tAn>Xp1Y4mhvw)o4NR@e-qaR!hYaJZH&JCvE~!L%vi*_;?Tbv!;jQmNhHi"
    "o4<j?4=rr2iw`e@?~dK2yf+asU~ZGNu1Kn&a9rcX#*(hU<AI71>kcNJWJozXjX)$I;tVwg_`{;Pb=Nx~_u;^neKzX;<x5dha`)A0"
    "D%(f*y-W(%v#)wN5ZOxOL@+%|iAbKW5#ey$lAy4cl&5etyxcJvw$HaUkAHu!O^N7+w|GpeZlgB3w*kUr@4|!!Z?FZ2Efr>a?eY+!"
    "8&I598(BhBbkQrV$_*VUngF{LJ(e!AiS){9AQO#*r#k~K?Sifk-(`Wkx#%C?=*e&#MJVLW+n_nu!UR-IIWdi@s3_!K4Kf4uu=2|D"
    "=yi(0Yu<8K1ZNoMBg~%mu8lQclLsxm2ro5BOTO0a94N4bw5*m3WgG-vhg3S9N_)>hkBbttL<m0Z;Y2DG3}uxO@(nO&NH0S0fD^H>"
    "xL>BVD~O%UY~vK12osFOeo;@9r-x9qKlLIDJ4DBKR~?j?G!6-tm`M@N_eMip(t9UK^h>PYvm=Q_{fz5S8wHl30g&^gMpxTco!9HM"
    "fRu3@KlRLRn>YQD&%f%X6mh_~d<1FVyJNzkwG3p2)finlSh9YJ9SJ(5uR0{sFiY9;A%No@g_I-Aq@G+DxsUOal606+KFhQN=YfkA"
    "mrb7$#hmw_?&vb)YL?lhOTw1{?t7w|w6xG=p2)h&;mgSVx#ur<8rW6RAvS=?{szMR?Ja^M<yF1OYR??FW3&-qAbdCxZ*vf*!f#RR"
    "{5<jF3T>IHCvJneJ@Iy6>VUI<FeH?mp!UPge!T%LL|YSWNK*CZiGMXDq%7*iDsQ;gkGBXBgOg*x6efe*eQ;xI&!UfZ@7MCJ)qRBB"
    "XE|{PlISi$=5~fpS6N;4H?P)0=1kixs<eMR2mXQ@1f=dkw%2cWag>fvwj_cQ9&A!RH%`ZO;KdN+;*{=^B{smHw>lgug~vy|r%aKx"
    "_J^9zpgmnWaNuMA@@GQ>`2*hDzj>|k=hrYaKv7mRR}3R{a%k1!H-cBUDm84so&dUdIg!#pLRkO__2>=`L^+6g8mK5xV<|fvyU=2u"
    "Hv#{3ty1UsUu=@xS01r}@+I^Hg0`18=@sFh5RUvb)H_r;9iEf;@vWO)bB@6?iAGPJ6Lo#@?eBv?B7~o^z8z_0!h9p=_LN@gQYmDM"
    "!2^+0dDa83lfQGdZ&qb|S)TL?mhQr}Qzwk-U!6ma+9KpXD1Sc6(X$3$Y1EFjnMVvQ>MVbM6`Gj&_&)wcW6JPdIwy^!3e%RgX~2-$"
    "=8f#}f52|IR=F8GodRM<^#{^h^t6I+(*+n&Zoc=gBQ+lpUbvGea_NZgP^@#Xk4g{72UkSYuKMWthEI!`#Z9E$);5~@*1WjwyJJ|2"
    "#j1yN>Cn$N)F#`JDRkSD8AB6-bYi%#jQ3WX%DE+d(y4x~I%eX>_XfB~G|D+>o5hC%6?Frqhhi-_A#}&xRu5CM7Sw(o&-Mt@H|akY"
    ";<~nRzJC&|t7amm62x!eC*iSYhK;-9ss2=k_*jcvM*B%HrdLnoVHjQXU|cnFziX(2KV(<`>@+Rp9>O$Wnw!j+%FV=CgLiise{eMN"
    "gWcYevgMSTCqzjNQ`ENIsA@;yELUZ2KgT;`s4~2{wH@@F98J<M76+yy;=rP8kILFT29vwaG$ksstAEOOkA>jg0KoTSRm!=-jUpb8"
    "ic?u=r^RDLo(6cKrNfS!y3pABU0rA|UszGL^03gT)hHGlPXEOcM#3XEukr>IJHsSVe>O?ID9susX?-k<e`%6dPQPK2q8(n+CaH2E"
    "s1(JaNeV5u6$c3TRF~|Gk_I}V&XRu9tqSv8;6>^{ZNF$3iXLX>ZpTF)O#pfJt0ZxFW?~mqRHuH(%Vj05X=#J<7$;#D@)nz%y%%Eo"
    "Wz~HVXLsPsMqYQoy4Plv<Yi?#kkkPig6YZWqz-RJAbS|wie$eXCH-P~m!34zF^XHx9I{1n<voxtbv>+Sb{mc+yIb~G>(=HKDOfRY"
    "oP29C(+a>dfpe%>R;H3OvllK@AlQJMO7rgXJQi%t?39KJCK%NS1AiU)s43ROysTIRjB^2*iyM@{y|a3mg?d7>v2bQL{`YrJAXrwk"
    "x9Ip;A7TTgmh4|ErwdUM62xPt_LHM?i+}HDDH2t)iG}4#nW+HQh2otcKnu~UR(*Uj<!nXy1$hmTxvL(Z2M}9@4omfEivYK44^sNf"
    "$8EF-`HD*w<0a)QDK->so&a!SMzRMlE0CX6poMJC28;X(X;p4&J-OKC{S?YG=*k}3%MXR-=(W;5=VmKo&?L+<mkk=24~566|1!q8"
    "3Rn9FT$8q`V66fQVN%G%QS4NxUs%OGmgs~o6X8t>_FM8EGw+jBXjl&hZ?7EauB<x;-`O%VuPt*`Z_`_k&>WKkKBx-8kK?yT&$%36"
    "<1L;T)mEF3*Lo<*<unFP?uC0dqEu6?eWH~|d0~9JOPjX@Q=a9ZKtGL;93Lk0{h_pe>Y)Bd$>Vk9!fQ)Q$Porup${b(L3BmKVml-A"
    "S$Qop4Vqw2CsO$U*_2<9nHlbnG4Gtmx^3n}o{rliUDx0%=&FOmPCmsvt_tbq24|dX7W2(3$PR5GLX0;QIY24z`7juZP?Ty%AG8Ll"
    "Bd7}k3mULkM!Q>~c~|DQ%uzFs6PycD93_^=Z+y8+giSX5)sC&ZTMuZ2ksFM$g@xUlb8d-Psot3o?_zU;tOq4yP6V5m-Y^}2g3>X<"
    "%Y00kmh}RG!`&YDS0B_u7jfDWCj@=5>WPc>1K@??!0h&VkE@wKVtTEUaSkdv_^DvOd2K4{OMKtKjSuwwQhoC_Yv3$;@I~2Ftby8X"
    "ZZ%1d$KU%8T&AO-7=8Utr?ZhKqAyn-2%ZZVnIyS)risJ?eElA5#KbyWttt>{eg?-L=vXrpX6ykXd#r(P-cit?M~veQM%VmWc>{s&"
    "-}(=_Ovm`pW1(u!iLbjiH*sP|Dn~kZPVt(s5{$4>#L%@{pktAX2Z3@D(yhGKKsq20L_%FB`G)8aG&BxQ9kZhP_q~>*g-A}!34&a8"
    "&KmFrhK}KpOOLMbRi7jhRU&0Ihr{9BDy@2GB+HuM1}uxv&bWGV6e6Tu*s7Q^Oq2*`R&KtsEi;nKFVqPk>+j#TCBdp8UI-{4hUzr_"
    "v5wj}4UpEe(wREQ7z*3s71weN`kh=f{USu`-p)pI{S2VfM-;Q~Htp7u(>$be-Lla(*{JuDcOStG+fAjh4A}s3hMr8B^fFYrM%Gd9"
    "VdE7}i_-owUus|x#z!Wu<8i1q4O)rVIUb_QbY;%+s|1#>$wP}NtC(D-C_cv6GQ66#96Lt>R7E7M(95J#yzv1Iw!!$w8gt(M4K;6q"
    "OhWuk`Oh_{m8mYb_kyQ#ITMLZnP7LJ(}SQYLog(q*>av6m=KF!u)SR^Wh&M_5{0D0$uXv7jUd~ZG~|hoBeQz42R)~bo5E%54`enP"
    "48qqVPdfW(=}N>Z^%?zYZ?}w13R92<Ps92`Y}za3k=68UMI<rWBUfpeD*D5UXt}nAoufcEG`s;E_T<z@re7^ZjZD&s*C~lq<si;l"
    "!sVxcoyjL7`1R*a*NxNAL@`m-b@AN<5i%nDKds1L(14HNrlc(^czI`}F?-!E;fUMO7?ks@kOi#y3cw1Q-cy&_)+)-j&yT#?JlitL"
    ")Kz4s{c>j7^8^=CUdq8#@SH3sP2NI&4%6g3=?Q-UT&3EsIwPhaOtl($<9k;&@P@Y3^+z&1CVDOt5f7D)k)86a`3aMBad%{*EBnOD"
    "tC-Jxx_kC)ALh}h<HD1WmK#oWV%UdM>zOK!C11~`%<RboFmYPVIjzN_VSd6=K^YIt=-Ha&6sMQr?$j~j;o+MZPN2D8jJ0ZV8oUZB"
    "HaH5b#t~*pqf(xzp4~{<UH_B*em&u`mj_{aV6rJo&{EE7Mc(}16(IIO7^{t<m2eVMI{ZM5$;f;wqsG3mX&+Fxy)BV2og2;)YRn&J"
    ")|uKf)d|HLB{8DRssMG_MXf&CIIHS-@KDrIC<Ev_@xA}W2~^@TKWLTDC<_E-4)AFGG*fPQd7`d;dt(Ii=AD`pbzy%u?@Lq0lpLXa"
    "%+RhmFVB6~wli-g9bO_|8#{=I>7~so&nW_mUcT4LrLrnp0m|8)K(D~pn4PWTx@my0GUJcp*-?gs$&pqRtbJwbpptIFbxfe~%*lFs"
    "m5mXl+v8Ov%Z_%_?8BqTutV4H>(se!qT8Ay5ih=@(;R>Gv^v~x>8y&XbE?hAvyESozfy%DnRrE&&Ro8#N@p%#QKj>PD}i+OGly42"
    "F%2EdX{WoHo3w&gqtsB|AHVQrZ<Q15G0ZYFaKx2|Pd&Sr(va^Jn{-dzW2)YU^6HYxvY|%KIP>(IU_+Xq4JmZ6n5y0>dmgB}SFS{;"
    "@A+$`s&71QEDZf0kYcd4s6sVm{kac8A^nEZ>MA)j9!`JXPBX)A^X7OqQ0U}4p~tJmRp5=fe;3obh(q~~pucK$j)sm2J|4*1_7?N1"
    "6L!YZuI7u*sTqMW@DJ5&qM|V0sqSI?L_xSput?rWq2ws|GxPgv+^Mh!hgN5Z{ibR@M5O3N-`o&tBda*|mxycv=;zm2{pSGx6rbVe"
    "y8B?umQC_#*NXZKAHddJ;?i_13=ssnh1RscaGOq===%1oGINgjK;B6dS<b2S9&jlWWcPt~3E{?eL1{d`J#JIiyeoETKM}J9BiV>+"
    "7SrnJRG<!YH<am|@09{$_p4tqDcXOCwWi&h=6+or@nu1Njg^II=7?0!2XdD=4l`^OvwDtAgSo1TduI8UR-HtpAjj~g)v6)08|lo-"
    "?JQe9A0qf!YffZMbdbojA3-911SeuMQXwLTbck5VvjM@{auvmTn}p))a<4_iVhntL&)_H|gd<Et1ZHO@+rG0YZ+5bq1t8&LYE|rc"
    "H`Nsjdx#^YLzN79inoPyrmGcm8NPkTpuMyzYd+f~;(U2X_<R{f;ihwge$zh%Bib>85>7CAPR>A@1-w=!u(|JqXN?e9c_DNKNAncu"
    "o3fCmOKVk9`s~8T_A$M63!dIp<k~t;b3(K%Hgj`=?+p?}>X-yeJ>gQO*MjRrm$P`kqkhxAKwS$gQgf(Nz=`v#-R^;7g$#3@O)=tY"
    "CRsci%ZUu%gqjY&&D|$Go+yP}<yMiP$TALM9w)7Z@|S1sV+Dpxh2zH-oJb62=aT7gTkHu`$gt7MdA<@G$-KAwOz;HZEu>I=hHw}S"
    "kf)%Iv5pC{HAG$p4{eIqP$5{Loq9suP1EjT_Ay9Wn@w;8-!m)VV4#>6uwRdVv<@iWmhAbLXNOh;gRLeC=?Sqrm)iXKf3%tv<KWYQ"
    "#u(RkQHmmrjp20qX|`cIUXB721=&5|S3o-K1)RFe3#1h=kT-#sd6$JHvw`yK1i?;oc<`xhWedGTijY5QPX{KZ?MI;pm}tm3r`UX4"
    "c2QpJt?OfDI@}J=tgSG6v@edN>!TjyGx>waI(+SP0Sw7WG8*ofZxBk+&=y%&_+1pP!nbS3e*8s}&G%m#>W0LA)-n9;WWJ9?iNBuy"
    "r~Ug##`q{0pw(m)W#UFwf8*vQ8Xx5W97^Zo^mINsx7vNA|0A~*E~M6*y!mop9|`=ln!OAwJuC>VfG^juyi@5>UcR9Xxt;o_!D)s#"
    "eWlw&!4`{CnUkBjKTTx(lV<ng_9)LNl-zDbrfxox<yE)OJBw_6rweSKujVb6;F0QiZOyVjyGV{sJi(R9M}PV>zR8(wN7?4MgXYCc"
    "WbRO)h~>(rUWu#01->M{Ah#2uT}<(CTD>9&C7auoOs?X2_?btpuT}CZNyd;G-uJw7!#$Li8!i}f!_j{5l^jkoC|8IBEYN?b_yg;s"
    "iXX=+su%hzN%x--gpfn6$~Q*N+<Xr2qrsdk?G{F>=&Gei>%)u)Ut1024n_#}igoLbYv?)+5nZc1f9wWzfpsG7u%*?ymh&Wp3uD4_"
    "n;n(IAl!<d#Py48yJGhG6K7$uk+UPKT5}?Xr?|LkJQwBwQ(~zo8`mLjsm2C+N;}Eph$$Eyxbh?#rp^Hb-2A`wQ%j+zcvP#Tyb6l`"
    "C_YOa$Vi8cubv12;6XCp5B%!`)sf?j2$4MbASX_->c@0t&B}X8*1^mjD1Y4+pHSzhZhNg2ZwThE*#_lDKv6zr$F+0~mC(pH>8ut-"
    "s2X~a8-5<pD}gb)#P20Kz<in+B>&*-K>)|S_(x~MM66d7+JAT!k*%tZ9cShOSOq;qOAZ(}XCnehVYHITRDOZz1!T`T^g%AmH3xEf"
    "!6{d;`?#DPZsm_zQLe~s#<0~iJVt^UHpl+q&@$dj%Kyg$hvN5-qT<j0EJqF^8JPW1_ky0l<KE)WP_dN&Jb*cUzHR`95FlNQM1UH;"
    "uh$JYhzwF9ppf3@nNOnzS2VTUB%W9~%P+E5wM^$dX+YV)*Qqi=UxleG9Q~t@)IHl;g>QhEcW%j@Kaq4S7$FROpUP(-7`_3A9Cz%p"
    "-;#i<`k7x+1pjK|>c~{K7J;&=Vp_JsDTqx*r#CvW{J<PH1&Bo3FUu*m+mz$ZR328jwC&Nro3|fPTF;~fHNFmByQngaT~Zy!EPUMd"
    "#QZ^N9J9TLF)y|ka}2=|wLKW)m^nMHUFsZ4!=)kXt-T!Gw4x?zULw3Z*iPEqXAz)#+FTSY1T)`dK2ID_x)ps4E<V1lJ%PV@lBR<}"
    "BMLnv>S$9}*@)rM(MYhO&hr!@XUfTF|5kdKQ~GS25gSY1T(sf%f%;PN$MQ`M$H(-;bU1d^#%RqR*e%G#+^X#lj^%iVq!3}og!lTq"
    "U+X=z$%#C@PIV-6c2NY5m~-pM&7Q6Q+}il1u~yLIp-_&k@;}%#k$fJrk<8w2@86B#I$~;>1!rly)-y%wh_6x(tE<=ruk4ow))wkS"
    "DIz63eIkUT^PGKRok7e==amL22o77oAdMxK935>07&W00Cf?f!Z49Hxr|1&~LCSK6o(_#5D^j9uVAF)myp*DS2{9to@=J0;bb(4Z"
    "cFE~f%8-kT0$>=fD_M<_aw?miW0+RpwJ@Z9B8n2+ZkVRzR3ti6?8@Ha9d!ErzN95j1PiN-hSa1#2N618k%IVTfIqxNS?25Sm-cgB"
    "ULjjJQ23!n;CUX&2(jgyumqLwsO;DhOy?Bs)Gm=|bXc*@0bpM*Q<L({aL}OTFwrw<B$;92F)%rccpWq@^K(G(bwSge+<YB(13pfv"
    "!8b(;M4qqnJ&b5`u`V5Y4TL`v1o~ZIq`54<iRzrO_y$aE6gAJFL`@B;&?w$b6(88MbiSoQuh~Efh~j56MVnhU`rynz0>cvcFM0qK"
    "C4Q(5gjspNbPoD^9JF?*W?QU$FtMNfkK3-O>?(A!0r!>l`x<G7*!#c)@SjRAR1@I@W>N4N{+bwGOx)|PAww9fLEFc?EDZF@L+?Ud"
    "zljQAo|}A=c;rz*uimWLshb|r-wd0FVqfbVN>o(NhIpd{VO+~_=PJ|^0PZu>s^UB(Hh&2H>&N%c+^MD_&c%Xs?Ds;a-%{5T1-{G}"
    "L|HoNKYX`g?@@#kY>q~RK^S0d8b3SYF&`JA1q9rh)^A-wN#|ABZ`B+aA~D%4fAr+ZVueDBk(2yyT_IXMMa?O)#Gm||s657OddL59"
    "tLSvML0JE9LdReJiT>qt1E$lW^@ly>FXm@Wg9Qx?zg{kK+Id=b6D?<-K@3F@@~(nQqh$=Nf~05BK$PXuoLPDh+8auL!aF(=M^LnY"
    "u5g-X$u=U+1glPE07`H6SUKd+v9+Q@uTh-Ds!?w_Q=pn{C7GU&6a&X|#~9x*r$K_eu$Wa4c?|pQog0JGV{|*D^r6>e9X3jc1*vp)"
    "*<yhGrhL5225*c|Hia^lIH*8{6-I63REWgmQ{~iltm|<RS*P068A3EVc27{xxQe#aj9A85#%Y)sh!9i^T<?XHI&1TSxQaqLcz!^`"
    "NT<8GC?Bt+dt^w%!`NpvMkY_0{#IkNjg<;#kt{q^2}oN_H)Fd=bV86Lr&U*c)j+n#c5^%L(ShVm9s73G2Lx<M7!_imRgIFkV1s$v"
    "e+_!$l1W|!Y_TIwO8OTk!djIn$ztC$^-mA^VX-lsfkw8jY%X36f-aIT00<fmQF(g(h$stB4rQfqkeFHk8-PPa_z3Ps-3C2V1jG>3"
    "GUF<UD>`5VvfImyft^UjnNw~E;Bd<O$4MvzaHEMp4|sc{I4NtkiX(4`ycolWBWnQABbA?*gwd$em|s-DdhM)sZ7}y+&)R*X*N;(Y"
    "k^&L_>0>6sn+gJJQ5OptTFM%mwhpL|Fs)R9$m6*>Z+#_95ewvRT0OS%I_TE6Y@kyiYVA2t6uqsVvGS;7<U{)3hFaY(LSoThb9&Gz"
    "6b)QZF{1E*Jh8q?TN^c-JHB3`rKj)I0rM-R?-T$PCe?Hpqbx#nI<~JHJXS;vCUdi4TI;^(kTbgxetlHB9(`&u29fV5I$drT-04Cd"
    "EesV`GwN~y^P8w8d(;z%uu%QN#aAAtQHp4ZKXwF_rEcxQt&cFA$G@Kax;C7X5ZaIT*ZY2rD)U^mfSrDi=cCOqvW|HTR&v5FXIvM?"
    "fB?gF&1gYp&|F<6)hWn35)s1<!PTz}gAOa-z}Bk01?H^m`UN$@50l8f5rxvWvpoE?J)Ih-9S7JLqyhYgR5X=UU;Ns9rng#S`n@B8"
    "CXXriFdedM9mi{x6q9p8EVg4rqA?51E^J!)G8Rmk+m)$m!y0)gTG(#GDZ|Wlit=%6?k=)JYxKk~v)!d-5Q4zNWis%&(1J}3yki?A"
    "?6lTzSR`gA#6jbddewPnf^3P=YQ`1zituqMD%-x8;#e}U2HCt!Hs|e;=Qz)J<gD9y+MhGWBNYe{0>pZc7iYEJBgi0neWapxE%p#N"
    "pQql|#~=;Wj=yZ}Z^k!6R8(gj(@N7R9;Zi9l!jTa{X@0_vG$FA?)MY`bP1zhb%Fm+UglZH{=l0fUB2Do2Cea8^8HsXJ4P=5zn#fH"
    "yG#Qjz?4^<A$1Ew2#sw68)VFOj+l^y7ix;GyMnLEvjD3?KwzwhBNH>IA$F1BJmndTCb8-$usC`iF`laQWhNSYhF#4|0#kC)>t_BT"
    "zIrI>^JIB7>K<)GZVellLb>;}npygG=l!jp8eRgT^P<>)@(4VF;ynSMc(Ig-73s>O{3^_To!gr``d@8gB?b#P`-)1$+CJ+s+0Z~1"
    "NbKtXtR~+0odVQp?u`IQq@%TDa8jCjHDqKaEJtq3wlQsWMLdl!Y43V_0l0R{;Wc<z5f*06xtgeU8*+PBsJgnJ5XFW?b5LMhE+B~s"
    ">$WR-K+yf~{s2gZHV7&}Yn|}cfU09gQr3Y?S`Hc-H5adA=2^|#3y##B>22#l_lCg4jo&+8Djgr<tXWmW|Chb@U{hVmvIYOjP?$-e"
    "m?wiByzt)Jc@LK)Wa3TY1;2e1P6`Q;=T!Hts@vU{?(cqeGD0CK6tQEQwbuqTO+D%)1xth2crHoRJ%;7i&w)a(T}7NiZhgvP1sZ`x"
    "65ciJirR>yD`4NlukTKIkD_;-Ag>R}B<Gc`5--sh&V=HELy<g=qfJ?M%NdK;`Ndv(&#TS7V4A9Zln)G)Cu{=<)Gk;H)wqdpnNGyG"
    "&49k9bL`AWR>T5o<SbI|A)H>Cr8+bvj?_yO_o!le{kD7b?qc%G43CW{x^F6SDl+l;eL`xaLd_3Xx|I~L0d}rOQ(5E{fuyU_!YFmP"
    "(CFx--5VZf4V8@8X9Jk#Nlsfq4$b2BZCUb0;GoeY`Eu_9t~n7hV2W&zii-ShGxr^+p>CE4;i#aA3f#oKFa7c|Y-KB-Ub$Ovh|3Yk"
    "Y9V<@`|A1KSX7H_f1Aa}+9?q>9}`53i}0G%OyWX(Krq<x2k4%C2mk;-0NQb|Ozd93o5N+Y0Zq?sBp&{;^pO`$Y(0bVKvWUN^Sl1N"
    ">-HUF$3Ag9W5QiAAw1-wuLHVjU%`{gs@zp4x3M=4nC<=YF;1^y7Oi3@(%R%z%(;7!7NzLI1Q9O_V;`WLgK-8MnunZqfsN3Z=z`^?"
    "8<K`8m>{>MwCC4o0Gl!Cnv>`Y88iopOUb7tgJvKQ$E_NaMA=brhYX5OGWDS9^&&qh^Vgu-K_7ZCFqnJv6m}!rH_}Rhz!M)_DeS}j"
    "KE5<;9rr-=fA7DBDMN)6B2e=siX#H2*tROp&ry&NTY_x_DjAqc2FI9C1;FxK1=rNrb<0MBcZsED@>mx$<qd(kI*)Vgc5$3rz+lE_"
    "jL(f<1Jn<toZ$Hk|A1`H8n>^5D*Huy_c~Ff5*+pS6tgiw(@EnD#7;L-u3Dp}YMv!paNQ;OG!7J1gFtVM0N7~^RBX|^V{KM3wVAC|"
    "`}!^!jXQISifSO`f_0^?#+#jv*K*x{Q!JEOS*8k{v_9s+kiWp(5v>eX4Ko4Hma$bMk@%fDz`i$8+e23~j`KU+i0ryK(QAl0V1)0f"
    "VZA0?M|hoa*hS2p3zN;G{@Llf*i`!1I2jNf2}m5vsfO{~Ap{FH*!+`l&})qcW3bhKT$i1IlA=dE<2USX1;-*F1(sbBEa7RKA7)ZR"
    "T=~j7vP?c>>Mu_M94mKC!!}B;h;!-y!i3Q3XH-M66<onk75nwZ8k05j`ranvoRKVEfL1`XhZ&bDj3YM`Oyea*+zrkfpRb%oG>YMM"
    "AfZNwcnA^fyD6es+K{VKT5RsC#$JFbyn>OUsDAguDE!`qjj<G?LWVHm7}hA<7|R1{kq>Xj6!e1d8)J<I3_uEOzzmw$80*eH(G*#E"
    "+8=vJIBIHDmn-*|u*M{iiE+-QD$aqdye%xY&Fy-I?#b8ega`M{DtltDrm=i5I$x=GXcE2HEqXIno$9yVVP5>bPt(A#L8kSkf0=VQ"
    "mSwQ!vhjdxmlwL1NoI!!GWb7T28deS=h{H$vTDQ<tGba>OmkW0v3dw0do%ZR8Si05Uv@pzxhx$FmH0eh5U^@5OS>z6=+l0>3`DO`"
    "9QEn4sH1NA=un<J<uVYML|%XGWvpW<ChGTx-erJ^%cc()*?0E8LW7{keSSCEd-*(*|CGxrv8oFFqJU-?P78}U`a6V2O)E@uliU;J"
    "hmC#xu?-)huG`^{Zg4jaT(2AdzORbkSvzT%xTM$j5F+JW^ei{z`k6>A;z?fCePl_&q;;u*BeeI9J{G?yq%c&x&ZI~!>(T@i;~)=d"
    "pm^pf_ye+^wkB=d5QhbJy_=?iJh(5eX~3a^-Azn$A&v?U;$Ye~yh(H6l%m!o0TU143~iaEhP9H|MEG%QyE&-$;UWm72Zu{PoHA!r"
    "cqjK(vw7@~7E&B{oP8(41{L<Dj3X+|E+0R}%6HqKCT5vc(Ny!x!qok|42h-wzAuzrv54moSapPP7R`t2W?7r*yR1Ucv(Sav_~HFE"
    "ZFi-ooe^$ep=v9fag7AY7P{RE7C?cxhE^m?lYbxjS5*I`xEtEEiwbyQq>Yu}G=KM1V@&lK`UeWN8?&r*x{Kp(<h_)Nc$haNIRNln"
    "(iS!;idy}<e;;Ltxf)}}!4=~i)UVUNnCWs0Y%=YmXuZQCC9v8L<m*?0RmAVqFXK<Y_hHRt*JwavyF!l32S(Er3td<p>;cQ`5*z|h"
    "hs{G+xs#B<@5Wdk$miTO=nDrvq`1x%SwNK8rSB21!-5Y1CfEAR={%K}@r1L1=l2*(-`uqeJiYl+1n!wS(i6vv*c*dtbHt22_}#d1"
    "DrJ@Bk6<Io@?eeot!+DhHb?En$ub}>L(h{5Lo^W$1^RlVdn{zcux^7jmrv_72vhyxH&s?kUC+H2V<P9ft~C7hv&yY+W4!yT8f9pa"
    "WYHpedI}%(!+WK~x?=P6jM2g7nFp}9(}Qw(oQ_45#P2EPMcVb7`!fb8=k+~7Kf&^EFx%U+&^CINT1fPRZ%-S9W>y0*dR?o-{QTgy"
    "HEjaQMsL?!^ne*x-<Ms18cdU?2WLYrNQa;eOSuebx5k_Ta#_-`mf5G?z;?9_z5G(;8uU`SBTI=p*QQ=^)Kaxl=*>H+L)r^8itDRR"
    "SClX8^60=wv!7>Bdo{au2KX5=MK8l*ERX6#N;?MGXIOLq<HIH1P|a6Jr$@?40YjCqd9e=-CWSx*DS$|}%&9xRIpVfqajDqCau^nt"
    "O(O)nBC`e%Z%7B)#*hKzK?v)JK#NFn?iqLl`d~d0F}K_teepG@TD4n|6~gf|g!G5cvTT2_%E~)g-3xgW-Ws?>2XjYA5JR^+O*KCP"
    "W627QSAnWNxgtBpeyQFuz)AY&hiy9XV*Q^p!_|;P?zm#s+X|((R)FUo;uEptyMIH60H}ili@uTV<0&I=#5p~0BaIB?8A7tE8Wso{"
    "7UMlV-8Rw`0EM@7*(TUVl3fWjmuk@?^3-J01|OzuNAcS<@(&a(+c~11h{SU%R)M-)FSTK@o?ACrP@kdC6;ofxL;2>o2^MLD{#`A3"
    "`m=8fk3B!Gk~in5c?!kQI8>=%<CpNU>Mc|LjgR^VUQsX`>v;-p=i=Ha3Mp&eF9t{f_0%UJQ0wxL<jSYA8C1u_uK8u1uVRuKX_<#7"
    ";q2S(Vt+R>UVi|_o=4c9BIZEZRtAt{w~*onOUVPuS+p7@i*1Z6Jx0rAcnsfgDT{?~Nz{aVn+ky!L4|j8O6{XH1wjWpXF+To{;yGQ"
    "_t_?ZI^bA7`eN!E5fQ%PtDrO-K&~GGN)!hSKS3aP?Hfs#z2|N`HtCs&`;%eU-J7yzvg@<B!&A3P8HuwX#RCaN)%3WEGvPw=3;?2X"
    "9=`X_zEQmxi=7~Hucs6il4Ts47b?;r%Sxmix<h<IBhiY&ZRZg4{q_xd5o*2j91of~ww%(VK^91EFJ{kJ!DFJr)u&+F0Od@+J$^fe"
    "v(_CTeqQ%j3V%w)Qwv3ltlfG(+6LEmzxg%~ELe+hrljfri;};2%;W)UhooY=V?G%}ny9_wWs&Y$I-ZI!wA2R_oH;R98`*}%j<*LA"
    "7~YxR{_z)Uq%lvF0WK^dX01*PI&^MlNZ}|2vpIkt2pbvUvwb>-xe4J9hI#6UP>AF4mTI5({1r1dzxQJx>Hxq)Ton%saKAXA!v{7T"
    "i|*pD<s2Xz{?Y3(m%%^q{J-~ugxk2@syhNI4QCLf$>v?WePND2@7RiYB_wSGNh#=<gkhvyEefu%x#bWK2Qf?+uOXaa9G9=Km>KNA"
    "$MgcdCqlqOo8z9WRzjeR01Xh$!20wGM_~`qq?LB-5F49j09vIj^~12<P#G<CI(iR~`cr-<OH0a2np$p+vKaN&x);|BYEJEs=(<b1"
    "pWBuVR6qwg<)^W+a<P@M7tXsJ%38+;TZLeO20w-u<sKxuB^+n1?YZ>qDHeil<2s$!yo-F<=f}KGm!AS;6?3I--5V1#s+GEJ$8dCS"
    "@Ts2ebu=K<=J><tA~J6J*vLH8cuMlAFM@a6yRz-~&gTa`ldb+*p2@@SegNvbNqV32)#n~f&R>M-8m$l)Tp`?Z+T(v7-|^FB%)j*a"
    "uYEVd0j}ACbxU7NzL1a7GR=oN&1XGXe)gR!2T|Xu%jUAvUw9u?%=E@%uKo`tOW=M9?Aodj&Eny}CAERhy6%grnnq07wI7VT*v*??"
    "I&<oW66&#2&n;_~S~=kyWcc@Il#l$}Q`b&!6>!Jqp|5k9yL5{;iQ|9kko{M&@TOC-<A!|QL3}**<yNWD(=T?uv98<>ozv8m%+pCC"
    "KoOV~HH?Oj+U;BK0}%aL^W8=*z3<lWHItba>yePPbC|{mMT(u_1>-YDO6z5>wTihBb`)d<)9Wh^N?3Uc9WmQ+@43n>i>#AlCY79v"
    "g?J3DFjzKCQm}k=bEvw;p9iMENiS$*!k;JE=f+vFqftSd0DKCHPEZILpv#0EJ8cRDvrj*$V@%_5J-jbu(dojz1=>dTT=8pVWr+Wn"
    "$HqW0-z1?mQlM4Lx@(FUm;Sa}W)|OO<60F9nGc@R6Rv}2hi6~_Y9#%J_^9l+t#g1;^>)EplrmD9Q8GM1RvqoQbe9tlj;?lQrcvYq"
    "(bFn^u}o`c8~X!|DYa4n)jscpnYcUy{{L^P17T-1+&)LPaCGW)=E6>|_31?izOW`<)8(%zmDe@y%fNJ%@z%9IaD8v-WX>5rBTBVW"
    "u&v-}S(Z`t$n$!=WTOiB*a`e4iEbllsHi2v@K*VZV?<GMRlN+%&1mph5Prr7#+v0DMMyvqV%-lC&zd=q_ZxL^A6*<j8y?T$LB(2h"
    "L%kT()hWN(vd$|62H$wY_MKrHA7pLu?h`O73y@&v%~opPL6uxDgDdt5sYEQ2I}8qP(E&^JFdMNOg%~#wg=1kN`CGF6J!ja{!-|Ij"
    "$Xs_aRYG;P8TUDZYl;IY0#si#RLm*b0pzHKEC)%^@MGp>#+Z|b;zc2_vx=$nJkL1S{8Y?3y?CXRr(r7^%3GbTr2kci))<U)%dv0n"
    "TOP_M`o3moF=>bp#%`2Df^7&iRHE~BIHpYj7_yr}y+|I)M26y;x5ujK#)-(r+(RscL>_yQj$d&&RB~9#-2nMz3Q~MPU=Wxv;8KWk"
    "c&LuETxlfSk}bJxdIA5Hq!MjEpm`XD`m!|CB!+@epm-thw5CyEy;SmINf&!_kO1_En?v;y04cCwb^4&6Cx+d!l5IJjMEue@wL3KM"
    "_Wg42#MER2)|Hb#S;FhtcVqnBjC4J*i;@Bfzpp~C{o=<0*~><MB|h4qSmLTZ)?Uqgd{aI*ZoG<k#Z1*eWj8b3)H$rc_|TsYnMXoQ"
    "Z?Y}-(E4U64jw6|n5i5r>d|Y<lsQG4hv}9_?`7h(kB{<TP)~M*-Q?~2pgyEPF$@kCY4iZRr8aB}O6mbe5QV#Zo}>lAehKWW3@n7p"
    "8njC3><a~nfM|Rp!wb6&?lzRfHaO@HGFTBf%;Fl-f0BMU3tYw#HU5znrt@w$2}`<5L-94eF7;*YBa_Q}j=(b#o$H#4kMUQQxcG&O"
    "<`d%`xF{HKB8~LScmvTBdqt_PT)mEzRJ27@x?>+Dze9j0Jdlr$kFG}G_6@#$49Y<quZjg!>2{t}i_i?YcBFQC*iT3AYqJ%2UtrX-"
    "@5JX)rp=<%?DiZpR{6i3ljNS&2^>?WW5@MoE9zj649ef$5}Qxj&?`ENz{(cva(2s6EY1yd{4kbqp;Ljtd)cs<eph{3HgZD_Q0Y+o"
    "0_W!5OY=^nNjQfTXcLJ>#~3AP*k(*KbNL9a{6-g2;f3=dr=lBfKoFP7s?T#VVi+VFx#g$dtT;J!Op_4^H}1$;0TDTq59Sc_bB_Ak"
    "Yy(mV@oA5^*#Y>{Z^{Albb^gim^G~#0O?qnQJBzSNIJvQ01WZIE%}G;0DL-HM@t>X9G(VX$?B;3OL_x%IM>Ans{=g0LgkPQckO2g"
    "`1x!X-naAsRPZ%zA60_slV$*_nDcs6|CAL$`U&d%Lx7-T=@=WdUrb_`gx4BK6h6%XE2#;nRJJ9{WpyTz#6kDbrS1R>?<DdbobfsX"
    "6sFa#O+MbA2Y@Fr8~}i8bp`-1^_dKjd>+8i#(#4%QUCJ*S>pBCoHN=1YS-Nj9{#W>uBY9KPhTx%%QzEQ&Y$;!HxT+5#s~R8br-~k"
    "7^q0ZdC(SeY0j`jan~pW)`@Y!+F&ydSxUfPgoKdgK$4g#x-5nWc<>$e|0IP*lO4>~9q5f06S)YetC>S6-hogkVBi<GH-eBKdxx19"
    "*fo9#D`2&hzhZQ3p)(qPfP0(P(SeH}u+)=7efc4%jhqv_IYB(|+M{&oA3jW6Fj9eOoLk-V&odq%F@3T%I`QWd)PxssJedyY9QEXD"
    "t#ens(Lre)U<yTd`da<Li3R|)BF_WxZ<swK?iTzym)ps@`ikiu+~mzSFZ72liU;0mwj6D@L$Sm}JOt*k?5Okt5cbQyt=9xNEU1+%"
    "VMX#l&LkW{QqRDI)qs;2#gzoVb>Ib%JVi4R2am?L9Irjs<ptM}7TmpeyHz4|fMUq|ORBK@(?leCD}N)HwH}M6nCoPx6umfg%y{*W"
    "nRK#ZoYu<Jx%j;MaI|duo;E6u5_*R}M$R=T3m|>0!thJC3tWf$SQhAwLQ;;xJj=?}1$hrP-m^dWLYR>(a+k|4>UUwd1F1sq{d&=b"
    "HBy{MFS-y166P?`=^|rSx7pUKE<{1yL7PUmOObSeWE#3%WT&Ms`l<_ADZAd_m(P;FzUp$OXbWD<3vp4d{Oea;2sCNYvAp_5n7bh3"
    ";9ebDcI-KH-b}Zj*9(q>>a4okxVC(~>W++KLDueg{<}NisY|8QFxpHX4Yj3}K$aHVfX)|s9z~F}|GD+m_hP!7u^ag}w7%Tw_0V@L"
    "@Q1ci6EU>>gRTF(r~19w_$Rmes(If3&ujf*P40bPKev*ig9Jdq|7s6xs^!<zbxH5Ut*D-~7t>WVLKX&6&d|4{CM_BMvZ-FtOtmgT"
    "ACO!;e$nvyp#$ReEoJzX=9Y<6+xGmu@GYmtmR*MUXl}_aC?~p(m4Y04^erjTRQLmLiQm$BSv=p;xBO{Unx9*BCsx+Z{*j6OC*M*?"
    "57leZSNcIGn)OO5L7#du=qU~OmUgECg?*{)Uwp-*>Bcuh#mLIHYEfhO2fo`JPC#^jpLziBAmkb=u5a>reI7RzVsOSBF=+la(xQkp"
    "SXbs#QmI!PaHN`X#+E0Yr+i3ptN+n~17NdaTj)G__rL)1WC2zc+AiT1>l~=|O{|vcUK<oM90lQxPuHgGYr6!~jDejEoY*=)P+d1q"
    "5q>;@9B0@#5yFk%Hcl|<5mX>eZ?mTXBw->aVe#@4IMg$Q^?sMZijxXR7BR8=s<t;cfIJ5){Q)i|qSs}HalHW;_qK&p9Hr)qYJdU{"
    "s4}AfI#SdfKw1Zw+K|c)R}CO9q!4f<AQK`M_oqZMfV2|tQ7=q(y_d$Udz>5I`w-&1Zu{2VGD^zY6wfMKW#_n68DEs6EptO#vdmq>"
    "yzRR&PGU|KhE!VRIhyrMyX(M{su&4Cp62RP?Oz0s%f5f8|MvFsh{JhEOH=lRcLy5bH{?BmCEWfR>S-vw|2z$)_n*I}{ogl~)}ySy"
    "aeiwL&PerP7TG$izOCaj-V0B+)Oph97yPTsAJgUen?HYFQubN;mJZC3%oFk?ZSRa{+<6{VptK2dsA=dRc4OKjSwQfY&5*r?{_6bS"
    "r?bUhbB?6WUuu@~EyBfoai=dz6$G@SCM=Dd!!e@yW^D<i5J6nlN5XHKKmetZg^m(|lNtLuKRwqblA3{WPalauUd|8}R<Ph5aEgUK"
    "cLq~w@a;8tDkmn+%UU}qE6y{&QaKdiiu1SiB&Q-=QOSgb>6H*JThgcFT+bv?<axqtpEJ0a(JRy66H9Lbwd*wZ!%%$FDQ3RT=AXO>"
    "Ajf{QuD&#sz)&;kGY?KW0c~n1m(vkyLL&UvLxuX*vL2qE9%`9~q!Ec{q&__qp6vBN{9&lQ3uk-~Hfr6WhL!0KolB5x>%|LB7lf85"
    "n)+d`tQ8Uw&s}@3r#*2sAy|Ij60sd$enGIif{+PSZLX@nU_xd+EyrFj29`hJ^t){2GxTy@xt%K>nH!e*mf5~qqBU5U1G*jv%t>dp"
    "v+sl(epB?m+&GNeeVqTSav&eMC9$y4Do6g8t|j?e@Gx4RlggfYrC2?=BmPmZo$QX#Ba-{;mVcI8x{c@5<<%{7_@BDBH0IDh^==8W"
    ">0|fX;rz-)`tgG^6cx)XfJ4fQ4k_eXq8u2-ZCD$2ZF?O(84&G@(Vh3cyC$|v;_|pNmDeckYz+=7q*Qp2ua`Q{TqyPrYLCg1jLVS*"
    "Rp)&CB0K@dSo7)@=vt#soqcBvIOal55?FCL`lq@%Zh7kL{vK;(J?{w?^KFkfeC|BPJOzdP8$QtzcDoyq`ag9Z^+5hlK*^kQ#^+_%"
    "tIh_@NW6<7dZS^L<6e$z5ORYhbgMwv5$||3`~1t!IJ;~w3=wjs&<MXCnQ?b=XxZgL*PehpTrWE_o_G^;VhnTkTceU~{m>aAKEanc"
    ")gE7{(!%S`jDX{OsYEo6%1{5$nXSvq408bg(3we)bO+*l`>8WzvX`D^D;|EMbF>&r)}(LFRDPo~lZmkpG2b7GztdUs`%iRMcK7Yh"
    "B~p6O2R%{n8=ZmZDJq2sI79`2Q=1{BVbx1PKYPZgh&-X^@@RJ?;b9|<$y2CVk~e2UVIQk6YbF|Xmk&;yT8L=Ddf000kFUqx0W&&e"
    "zAeEdlUqO`)DeYzA0>TIlx<n(`be8M)g8W@{6J9uq%s3E4;1|zVfMC|Z)((kpqaqQ8ck9EfxO~_kL_E?gMD-N4OYDe0x1#Xsdn3%"
    "-UGo0O*ze92&L(0@oeDvfgodGm}IbR*|y#T!T$x6cmxxG?4r*Pq(Vj(SL3nX1HolQuvWsOT1^$79|+D$wur+Ng>|i`_dqa?MRvMy"
    "^;gcu($fRMk8r$O<!S%cc_2o0!bujX-UA``IU=tE2a5g!LGeRQ?lt$V`#^A}JlD4~c_8*vxjC(xu*H<}K*}!D=r+0Bd;WkQ2yD=j"
    "V!&#F+-&Bp<u(R`-?o_9w7Wfnr^lD0+G}&$d3H7`6Uw)ofJ*MWuWT%E-EF^%{v0b73wgytS|M~?jt$^<7Q79ZapEPW;sZJ7Z!NYV"
    "$7<iLG-0RPoWt@Yqr?dw*lchWr3sheYbvro4xixJLVd~PTxCcTKTs7C!vv+U9uEH%FgjKF4|w~N5BLtb1pV;o)m;eB-8Qi9Tt@G}"
    "RE*j+sYqmlKJFl{2DWrmYj9$6g}pEH5-|s9=RubaSply{$;w&vFQ4T>h-C$j2H!6$j~i!V%fZ?~(--qHu@b5p?d%fh?;<=Pq&3=a"
    "6s5iq;~tcszw|9feQAajF#Cq{oF^v-BJh>g3#rn$M{u2N#DovqXeg6XtvcyXfl|)`)@~-2xfkcsEv4hRSSYE|HBQ`{b_W<*UTvwP"
    ">?k|7hteKb#?qNoE^2^J`8NPQg5MDuxN<*2iy|M%(o73f<2S(#&hbj_ooOA{4KXV)sg}lcabf84p3%i|VFn@0=&Nn5JS<_b(4rx|"
    "R)TX!D@)r-4%?_MAnWte?5-gLlTND#`xSP59XPm*DSL+F@teB^pKXc9!uKNZB!u5X5q|vKDg^wQW;*xh1o-@uTc6gXs>{!<U=LJO"
    "hmfj5&7c1eLPF)|LkRF6{o)X6c2~bVgu;Vg9zqlAFAt&c<_|f9vcEorx}api*N>wVx()ZC^ux34ea>GVLT}4o9zy3JlbfvaKOI8-"
    "8{=il!PkdS&Iih+$*kqNhY<7@vV!mBAp~;7Alc6WR%g&Tggi>El;|vAG(8<c@r??rK0bbHP^Nq5#Py{)gi-;Xodp+*$}xO$=K8PG"
    "5;^lCee;SQ?uXPxz-d<8RC!;mVi~{aQ~y?Dmi2x^Qa$Z;7sj`6TsJ>=ksf;ZZ5@3Xow7)&BBF(#fa`l97;ucQ>0biZW6X8rW-fYy"
    "kga}2@u$xlF5OqMGKcf1wiHwJ({b5|od9D|)cLXtw}=c`HJIs1C}Z{?A^t-bM8zezU*9NH+W^*PrEKBL6PlmC>QcbU!^*PMpSrFG"
    "O<gZHH>F-9a`U_+M!2M3bjjI14X+NXO(uB10uZ=hh}$lUPyNTWhY^g+=Bt#p`dv5{X9U2KDf%x>a&#p7ihngPQyh7stD0(O7l&<j"
    "Z|Rp^d^h2(C_|I<zjX2=kCNK}Ki5#V3s?6dQM-FAt#|$ChjS_0oYCfs0LdhxbO9T%1~#AzagkE2XWnF$twaRxxoqPO>}R95Ho!wS"
    "zQ`?PE)TLjp<B!{V+KQ0JNe~j_wG+CEJO_1lps$(DX|5t^tK}`78<1>s*%IzcS_W9)W5g`792F2pXcfn)DxldkE(KbxbL8JqcD>G"
    "{)Wq`O;pBJ40jF_$t#lqlBoIz6n{qNWZwTEToi0eO<^fKEc|thUO}nUDz^?k+i%t*s8?EghB_ON55wzt^G-CaU?_CU*!|*hQUy^8"
    "`4jyftiPDU6t>Srwi&*6M^2jIsO8XVUg!|_SzFuNBQ>Dozs1!~($ANX4uO#>{*~qk(mn%<KSo}aFb@ru#<Q^3K|3YpxSAY@bfPC{"
    "S(bUomD=BY@u?Uq#=?lnWxlD8-YWU&F`}Nj@7ks{g2L3BZ-&yAQ0m|s`Ge(76FcU>GOeR!$|y;I&phVze|p<T-t-!eR_H!Va3e98"
    "27s=fDk&AU4bB8)AnEAfTTaUWr10@8MbxhK>2fQ-bn_gMbFd&T@YP8|7IyJVYriodYRS{hnW}M0X@uIF|H`4PIsdgc*C-p`uj|JC"
    "b@PAA%`vBdVuS5e3ZmyU*Cbw0=2_#(N2p3jk1;@t1M8B@$eYjb8(kQsSW2o@Q{lf|MI&L@{j1Bry9-Anr>HIy+gUh%LTZEnjpn1e"
    "1P6d}3Y_pPKHPJrtcvkSGMqu#FdOYwpKVlxXx_~AeOb6d?fRf*3n2Glt8+j`3gaK{kiP)@JR3(|bIcR4IF&9>c_QjL>x42wJ$!D0"
    "{6U8CIuT%R+f?;-t2F5>26ub^l!;zwIaG-RZ2XHleW5jB+T@Lz{V81YjZWyRTx{7(_1;G9A89_*t!N11fkj`$**d7Ow6Ok-F5vOV"
    "gDu!^wMkWk)#FuG^g*Q{u#*YmS_MB+Y}%wkT)7e#g%)+VZ+O579;LY$S(nfQ#WisKTeGF;)!OmV_g+u2iJ5fi9r-k=!rb{oomOga"
    "kv7TNb{!HZ(LUuGWL0q$PX`6N`km7l#eP?|_CuxO$$9OFEd?Y>cMS%$9yDc%1E&JCO12>80wXnZCQBkpi!%7^+=t9~tNaMH?)omm"
    "GJ&^xaG+(8k*l*vyTfJe0fu`m7Y!)50?XdF7*0sUfagTZXv3#IdOeg*GPbr@wI73=L#rw>6bkQ6i(UUL`Vf)MDVera{Vt3<NOtt*"
    "70C~uBE_{AqgPZxIh^B@T}@Umy0CbmQ`H5ZQ-R<%#I!aqez0N^RS}Wwz!rkgz#ZsBKu=iuQQ2NHD-=qU0d*vxGgwyJqsA9kV4w8h"
    "bPFXkSHRdNwkWTRZ1r<kmQq|Zl6DCE-oU-Uk_1Rp-40Gq5YJCyDSrr8%Yw>sP`*K>w1#s(Bj&=GaO9<vXC=7@@!S=+BJuutMg%!4"
    "GtawBwlUyiLwlPLg!u5%=f7$#0>XU9-#$?uQ}O=PW%aqCq_i-I1aZRIE{Xjy1p`kb1Tg!zfJ6AXVmAmW$H0BjlS)R%e(@Zp6&{dS"
    "(e?hA1iV~e1x;(zZ+P2V=qo%c7OhBF3ZcHNF+nC@kJXhT)P}mXp{hk<cp&2h9+>;v<P>CLkp&8oM|+OV{#IG}Rr}qI1@nLpw-XVI"
    "w`)<h+)!G_V=?n-R6$MoET&I(O{0=Aa12P>+G9e3<=ToAD`M0WSGxr_n1MTP`#$3$ibTh}v875}WWSed^{GIXqdhhk-4CB6intVJ"
    "YjhV|3|WNK)+EbuRcaIBM*&O3gyAhHFT!V6_0AXsMBp{Jg7I>!&$r4VRDO6lLL%_N7AhffMF_#6EJEc+eA6)oWTU|E7R4N2GG)B_"
    "N0y^NWqlG_m8eTso)9v6N*^b@p`yMN!pqS|dCWbRQ74b90qFeDa@@6P@rmk+XsYaKmLu?qE5Dd^B3bM6L{lyJ+DP?)_A#O(wZ8XO"
    "l+rWy&tqc>7bLDD>S9k(Sa8s&{Ehe9i?Qq`SB3PKA*CX{mvuIsPqq?35#lq7^NP7UuTXY+ap9kR6l<N)dO*OHtMG4&eH*&~yhkk}"
    "OhnE4Bv#6{DJ=r`R~*xUQ@=EM-_>y@NfYC9#SL~xgr8ut$a<6dz--8lA7QB`6p~M<TALIN8hq=Yx`j^^^|-l4Mtv(06XeGjn<>6O"
    "=%2Y(0deDl5YG9vAqk{nZrQOs5rMn6l`}5vx)-+agKE@SN8Owa0=A%-+C?cVhTXTG5aH%12qLX_t#_#?+_pTGw^7{r)G55{peW5@"
    "l2&2W87Aq?!9+OJ&O{h2?8?aw^4LaE`Aj9O#vUL3zT7Cp9@C~Eahtdn7-a<6C!>~FQk8_5bZVgK6i+m&TQO^>x-3&*hjkDH-9cr3"
    "YZL_>VuXb~A!cm(sq&PP)061+aJq}QOCj8&G@@F`mBq#dAipIw%shA&Sm)jZ>bN24O1`k-7GyugeE*H;94v;5iP?_@a%KAlz1>nz"
    "kHor;bf{S^2T|#g!nWG(8=6%H=>yGGqMiT7NaT3C9%91%`x9?s`09U$D>Z#w&4YcT&0NzD1#DBRkUxER=4NyaL_+n$B~-yd5`wBE"
    "o7ivR=04my8|Fhzc=P-lSZvRwVs#EMb=6rNbLGG30NRYue4kOR18rWZV5d*1F7o11X&iuDzw{zyIJ|i6!1eeS3k~gqQeCQOD{SMc"
    "JenIR)Uvilq+4!j5w%#)k@@IomS!#$(*!GXcQa3N-u1o2&-bLRF#@O$52=XiPpMR>winp(g>g|cCMgm6%)=nr-!WpNd7r*msD`T-"
    "`S0n1nwFWB^W=Er(<_KJT&q0VziOBp;y4t#7luz-nPk-BSNO1K_Yo<;NhK)DkCGrxMMTxCYRh=4=)?>b!lF9Wi<R>h+>Yn$kMvP5"
    "^Xm}mcz95I1qN9sa^@0)d}*;waYNw7X;oz0U39NJ`^k$mc1dRAT7`P8>vyoo|38#c>-@VL6g>fa->|X>K9Z^?xkg*`jvMCbmULqW"
    ">H_Pc{MGOeH$2ZS_!$5De}k{VLB*KmfmaSX#c59p3^p>(Pl5{IoJT_XN38P2eNFpCQp1q-R_9s-MaFFdq!JKbL_P0BrF~}dUZ&sf"
    "i#%-u((L@n!I59nUc2lqn+i{>pF~nY`b66IQoY@(EbYO}9~v$H-X&wNoNY;r&x4AO@>9!aTx?F3Z?;mCRD*Ngq}?*FDDa503>qYm"
    "q3Ov)*H3bNNhVG8qQL2ZIuxanKDkBVF`zwQZh@0*-msFZ=h0*<NtXRrjCSn+W@y^00^QHPH}G};587&+vej_mMyTx!4K?`~g0G#T"
    "T!5@Co%*ZcA8dFzyWnH=NX-;jB3f0nC^kKmV`BWWdn)6A>1aTDdCse<vCVen>L}5Gx<bboSIn#QfKTd+Qb1yM&qqQmTsvD-nJhN5"
    ";d%<r{2&2rN3g1*Q)q2sj|RGtbA{88*&z656z;4Ku=DF6i4bozRsd1%wQ!2ZKEG2Nlfy;(6FiT}Mid~dq7PQ4M-n?ctPjHf{ck^z"
    "qx{Z)d|=c88kPGytf%Gv``^;F&eu?8$6Ns|eSvK$b`5+H)&hC`NL=(rTFBof%!+3w)h=|PaA-Q}mUsz_KLno;F!KOj4;BzYNFOn}"
    "xo#e2aXq*v-Tq~{>msTUS5`;Zg#}>|X8;(^P!jSH;}})yE%ZD{{m6x`0b<I2b~+FMfKF$3f2~v(c0bb?5#j3^lvlbOwa#W3D4zl+"
    ">lD`0d%60hJS3)AUw>V-6O7_&E;DlfEeq9X9jm&~ox@t!6e^J1C`0L2=t+tC3uAK2v^{K+-K<CIMxZh&SY%TgP6BVl7totW7JXOs"
    "ec>22$c>m7w!yF-8&+<_cp4Kte8K)rxo~pJ&RcS6-Ib!&+gI{HDepW?`x+se7Az&8k4p;*<aQojk*Xb(k@a}oP<e+JJZ=o8uF~Ui"
    "laZTxJZ^Hv+CS-*@15D(+lq}`aue5HbIb01#9=9v3tc`{w-oNzk<HY`>L6FM(YM?+;OUh>b&T?#b0>96>~><Ymm+Ha-YB=MhrR<;"
    "0(~%4J{#q?G?73n=4yv^{K#8IkOq&7*zA1~or&EL+Y0zoG!rWaAKdkmPrfDL1wd7BVhr$kMDQ&aHS|El58@k9w{+*WuzD(iUBWa+"
    "a!ZgoEB({8Mo}10Wp*V`tjReYPZG{IQx22}>hSc$?p@i$Th)(_p228quu&`4+uRUW&#o}juGn#&V<YdC+PQmL&PUiHeFr;$MG}wo"
    "VTp%yp+_sQx|NdF^IOoLZn^=km33;v$k6ALu9e?G?dQ17%NstE5ldnZVi-3RkdN3-52zrm29GLdWK!Q82unm|pC8+o&MC_sdq5YT"
    "#Hq=bJxl+m6A4)@bW3L2)&vGgPO@LkNx@=?rzy0|IHxF7al6fuv{Ed4os{YZNIMgj^{C1Z$Vulnlk{TMV4c1Yd$lNnD9U@FS8tsq"
    "V|R#7qIqwDif}CvDNODo(Ps}ruP(-h7s%*ZK7?v#7nx#qqr713oN(BC-KKc|x>_#+{)A(~4dDiQ2M}WFjc%9Kh^|%$l&?H)^+ms)"
    "S}{@N^JNOd#J}k>-=s2S2m6qx!`IuBI(1pB*(1zb+g^gcjJPG|x4A|1S7w*3e3=;mA5z6a8WhXeQJ3Y;*CJIjtl-%X@nvipJHZ(%"
    "13oBgQ7!`{l>i>#!<Imt-I2?jm;eN<cA&JdCFL?4p4eH!PgCN`8Ay5NWJEJ1Bw)#5RY5RVO87Eq3*m4_&kJ49L*+7HJT@r|RVrh&"
    "kSXDCMu>Z17a(k%ni9AD9c(56p;kaSt)21#aI|V&a&iae{H6MCY@NidVvHkYju8De?H578sE|2x;X=l7cjHtlgMbD8L2G3UC8OLi"
    "_844bkI^F=cvFxVL%Qz4ZbbGw7l+kq`i;!MgyiDKG})Lie5&h{<xvbK-`=j_cz{W}D<GQZL+Tnx{^!K(>TB)x8mzEdQ-+QgFHB*a"
    "Nw#|+{|(MtT(`_POJ!#a(V?~N=LeQnT59J@P`_dCi;<x;@{NIYw*kh(r}g`K+Sz7aU5ZB1qE^c(w93Jo%W{>KWbJ4&VVs2yEM9!T"
    "C8fCX6$KL*&V&Spbuo5aqNeKN+ipl6pu}D)u}yGo%;RQjSo`)2eS=`|z*UWt2gdw?4?6+sybDS$V8zOki%ZVm0+GqsYqVvW$emX$"
    "w}VQ;GYtM&P*6T@H_xR{5C|*lG?@38%}hReKLLxSN%3&R&EB9=D~K-Cz=?Nto;0K6<STzulK+)WtoJv)YybM2wn9+w<=?>Sn38i1"
    "Y<o_D=06L6B1H6rKM*2+3I9K*@R!eeTKHql$9v8_)q9Jr>#e5(o_GXo7_!;YT+-fVaz$qF-3Fjq<#vnYU*z2;v-c2d6BmH<&g^1x"
    "(XO!DaBd9M(c7pVj^oQ<<phNglIhB>4}1LM>h!K7X2+m-E{Co)I_C39Vm`8ssR#^uvtTh4d}4J_OL>&eB(pH6eh&?egDOC&vp<!<"
    "A>sr1r`__q6gBpl{N-@Z_6C|;682@9nws2l(WGV^8&ooLN!oehL$wUDA_2YAjABvYj}e;!>_Z70_?CpD8#B}4C_26+0RRFZZ%1}&"
    "Kh%aRekzY)Q+S$KXRJxVSTz%i%i&?36wSnrHkD2jg#C)o6D!}+aV-8DZb^&i&3kk`cI_QRSJ}|tDEVc%siLD`2Yi8Jo=3;LY@o1N"
    "dvnGR{4_3fZgd;ZSxK~boVcW2qF<6MJdX!Sd4L*~b|Zg+S<fb-V6a8|$?r=szy2xj0jEy$&!>s~FaJ-~(dtWS{t3R#426drJoq^L"
    "-+5lK9<zIYe|C{!H<*IKoR3=}M2W=`aX!Gv%3Ul2ycs^?L_(*QFp}vlJ)aGy$>nX7OqJjGRwQ^CgY*pxk}wJ!Mx7=CEdpPWhvHuH"
    "^;RAQ4yhb~XaF2*`ENSFWv)QW;L-Yd@%Sy0a9|M1swOnTfM$$E@S(nEn7%|Zr|ktD%f8x)r*v3*#5zgkjAFch9=QY4aesD4r`eox"
    "HaOv4e%eGo?YMvJSo$x~D&yG1nCNo+W33Eh*ovtO)6pH7Po9H^{K6U2YmE!{;+?MPO||-qA%EJ@)_>+>zAP4+rL<n_%)6OMUu)}Z"
    ">b2Uu_3!DEnxGJu)glNkQg#IkJxyz9z3C&>I_x(b(>l+*B~=4AW4-sCZ*omZ0<9}Xy;e5B8v#l=%IeQ#c>#+)_%Vo6^A)%g(z@P~"
    "o3|w`B)4pZsXRgoC-U&;R<J`BPp94gv{UELd)h5QdW0L9l)MXilIXAT-N;xz%dPFAWKT<aA1f{$?6tZZGRqOPixleK@0iuPL+<U~"
    "XTo^?YA`#rfX$JPd#_ev+lpX~SXVBJ6@aAR$~tX@U32}sfV?Qi+t6v^%kvb>6nJ39KSjkIo8K6=mqU?it6<xH5wCbOqf)X-mJ%jZ"
    "h-PUbhjr1QQh-@xNWye>vA94~u?B*_-}PxtaTNpgeK;HlM;H>xG^dGAH6P4<uPDeB#`O(~ipmj7jp~|b`=GP0g=|ffCbmg%dYY`U"
    "VhdF;I)-6L7RfQqJu9|c1qT!i<(3ll0em~$f3e3^spafl(U_#~=Gv&zXa{lXpNZUnO1KlbYJl#{2EbNX5wjI|U-;*(qOs^yd*d&Q"
    "?!UQ3w+4%Y*We`Ju^TJ-9p9gwnDxF~QMJEZ^+b@WUKFnE;|SduOGF})`nq0bq;+lret01Y@s@7aaAT8etXBqHr`;3dn@NO8Hj|Lf"
    "39Cg}?*V$-%naK)BIi+JTsO}YI*_w)sc1Z5I80hNItU>}rHAAmC{zy?uWvyji8c(&@%oxbcP=zmdsyO`q;GInjDqKP#ez)Q568Qc"
    "4QM1d)Y%?csyN+iXL;}r@dA`@A136B2UBo(X@*?5x+}JP-4g^B%J$65zJvQ1u2G$AhUE%WZBQq_gGPicS`zKZ4R;9L(S)V8u58FJ"
    "`$pfo51X98$?~R?P#(_0(IVR<sUP5bZwO8T2?OAYrGXMp5CSUf{1=4a&krG>Zutx$pb;of5Q0A$=*8{f4$oW;1cR!qSj_6csB_4+"
    "e+3-=Ck7mxe|7`}Q2bl;;-XUuTB;i7U>Wa#0qRA<8bf-33(hI)0;g*5wCjOt;C|)e853^f6PjN-tcubBh%wM92AM0czOl_V4aS!D"
    "^AH*tg0v2|tw9+d3n!-I6|KIZLP4BQHN0?EBU@#qt?to{GsLQU^Y1unUIjE>#WG%mG5(O@)s!|$rCD{{vp`FtJ@|w^jLP!J`qkHz"
    "-Fou3lD~Z1*>?iiN#(nSw8JWFrU)2it{L|mZ_FGVh?xP8yn8*9frq}>LNHW{WxJ0{up(ycH;jN6DiZ?}zZU>OMz|@bpG>X7cM}Pm"
    "@OQYS;G~9xA5#()JBI<gu@asd&C-+YOg9iZj8V&^0n@20y~a1I7$-@mi>sU)*&eKgOwtSi&~4*rA@i=|nhfW4ns>|jMQ$_^iR3ax"
    "3{yE3dU=MGF_>Io6{<9BUy?#m+|E}|Jc^rzwD(4#(>!Gq-Tm|TXX(5Rt;+bTd?U0y^LHPFD<D@n_NU5)u$VvkZ%N}WwN%-1^`YM1"
    "{uR&iulid+=WiGd!&~llw&;%nN&&)&3iu@wmV+N2Eg0aNYP+o$V_}8%)nb`C8HnN*z<bSW>#cf*$Y*_L@?@{z3m*u}8qffoaNlVG"
    "!Lq~eCay!VpIe`m9Bd~44`@Y%4BWT66;m{E9Z0_5>Zw{;T=L3k-1b3f=1+Ai=4bHTJ<<u|N?%p2Oc!nc{C;Bh1RnL1x|P9{w3r^K"
    "t!Z`hpS2BP9vR75<xvv+dV9Y{-qW71%EQv1DXn119Kn)dKw31?8o`>Ot!Wh5AvxD^Zb#8T!=Mg1n?c=Wl6w!F-3Uj@<~KV8HTBlT"
    "xuk6Frn1%f)(hJcVh<4xAP|19gFp$#^p)fadWS1Wql0slxWg_7#0O-k;So5sI4VMosY?@MIgLw-p|RK;Q_1l{-np0NaF;j3EQp?I"
    "D>}8z8&3aeu)X95bWXi*TIQjN&#=~zhvG#7(LrSB6*Kmkn2je?8Ko`(1s^|rJ9AER<|bm?L0T!hrETEchmvX&qy9Q)G<tL+ja`SP"
    "L+E)YCcl`=44#PzTobTNqZ765a6)C#(K6tXON363-@Hem+NoT+<F=E&^xRjo%G&~JYrE6Zg4nL62pf$&6@V}FIJ578>V-Uv&P38E"
    "jW=H)@9spf1d*kQ`D~GMk#*7AhT*27``rYeWlsZb5U;4DKD_r<pMb$-=!$vIDaAlBZM>DHbF%57@gPO5bjyfLs}n}1ukRKrzXO;x"
    "<R|%3-I9UDr*;^@=dOFFR~s)Wu-or1`j(2GzfCorHr}-WX(!Smo*!oPEy1fEeS5%^n*5No7_p1J0jUB<YzfSIfnW8o`uIo$W++T$"
    "`)CA2<(7)|ZhbF-S^%yHa(sRF-rrPZ9LcMSnQQ2Sk<^!)%6w7fRm#*OTyX8ZL8erUsg&s-F#VYig}t!4y_sl}`%yk}W@{T$3ajRp"
    "GQkwQC2%r5^lk|pCqUf!2rrM@1(xVnj9$@aB-j|r$467D?3Q+4HSew=-L+tFO{tW3-irYoP}{}j7cjL6Q?#s0Bxw2hfowgCU;OxT"
    "w{0DTjrbih=t=_gwqr8mES*CxRHm>@$35p{8%q`EGU2Ju&DK-tMh+?&+;jR8c)B19B_{$1?0>7jA2d`nSzL{0?a%^l5g-^`25`R="
    "XIo=dddK2FzdccgjBij%r}(%nzC(4FsH}za1_YcObJ`CL?Wkh(;j~%SNnG-EXTr`p=gHp2>1Le*a@d-Bj`L6scv+dO(UVYQi&APQ"
    "?>Cu5O6d4trtn2`kOB7x_9kN%Ul3Fp<1Bo^&~#CGWgrU+uolMfsma;<#2WdS$_E*eTTD;V+$mQaILJWh-7e+oBB2oGIAbvzpk(WM"
    "!;mBz5@0c$+2B#=X)vb<f<dq&RW^JGrK<;*JJ!mq!x!4L#29ZtX3jM&G8-Bq_Q4V9npoW(lY14Lj(d&VWXboeyR9kUS`=<Ouwu4?"
    "B#N@?Dk~iFH}`9s(i0s)^u3Q}7w|P}P~2|JK(C=4K}%scMl6YHQyTlxDqWv0m=gJrc6LFZz$bnk0fynQPFuR)I(b#JVSJQD$)tk8"
    "tW8U-Z5q(kQ9O$tZ&HQQ;^VyNU7vf0(C}=3x~w&Vx<Wq}x`xzseFMj{G1DD>*8+>xlNaww+s<Anw@3{a6_}pcR*HIMDhmm5i?=#="
    "ulw-fckpEi|BM%3R&bVbN@tKu@S!Exa+kUNbMa_W+BLfhQj85)L*4c140V~jN2cwA93!}*M9LLc=F@{KQtxW)Gqa8G0E^PE<q#5@"
    "jH2L_ah2+A4eK_Ava!c3CLdXd%Z83}aPhmy?0rG)`2#xR0@|8+K1PFj^9;V#4P|z~{B@5~d>zrTZNBcwerqHKz>C3?$^)s?@!3mQ"
    "<;Ll7Uy^#;Zj2(UDx@xuzgtBL=iT^G)P~+C*mt7lgX8rGim{@u;Y3DUNg5_(tnRD%kFmVWF$Rii1RP!&qU_0kM6{rSYHO0h9Dtn^"
    ")r;hI<p**<zuA`=s1?cLU)W6I-Y#-O0niI-@PAZN1!X?sk5L}7n2uG{ScC#sO;Sk$+Fvw<7RijC>b}0Du_&+V{7=qljMw9oMpj>L"
    "?xD%j%KfAtWZS5O7h-ge!Tjm9l4OrpQ}s+ywQwJ7im=UWM>2V#hdHFWgFNtgL8Om}u#<r3MAG@4$nLxRm-r8O{5#rwyt4T~r0m@1"
    "MDv}Jxuw7d@ti2&EATzni!f>cAyYX^o$#O~1PA4*#;W4BtfF1M?cwTM=q?^fv)}z;i^qo)HGq(yT(c;soZq~?X-GkU=*X)!U&}%m"
    "E$>P;XdQVp3-*AS;t1k8-+QGfkQ@mMg4snAMtqic>^jXj4`w<A3#x#-8TAC1Pl?2iG2zp4(*to*742O$!~Lc_`p4%~T|lXdoDRT^"
    "t$e|n9>I34cb+>jXD~_MExCFk&~|;~Z{EB?_N>S{1PA`+3WZ{p4^e&0KM31~bii|<dIvl@PD^W-XWts9eVrnPiSp+>;rIgwx9Dr8"
    "I^U~8n+x2sh(bb-bRu^$1YXe~^;_fgE?N=_r)4>uG|CiSg0<6*M=VqY7pK4K^6$FF<*>HrKfTAk`xWyq<m-{n;~|d%k+3ESqb_#2"
    "n%?uN?5$kvG{*hN7mmU5iJ7Xf2J$w5Eavh7ST>$Tv?NyjO2h7$KP%WT_IgPjpmvcM9QloO#oUS%tG4ldRL2>EaO7b|O(4p$gnl=p"
    "F3LfG%36Z7Kdb=*LTUbu#?KA^il_Qx8VE((AJy<YB}h6gUpA1nIAY~}#zL!*Ri&3_#yL*6Dn0h~>Xy3ymt01XTK@jF7Eb@c%l=DD"
    "$qzr2fAfb<$q$!(%d5+SR45K;AYMS|!*E_c6o{ToRb~+}6`_cV%|-wbyEFDc9bw=Eu?(1HR;<9>YKBWEdja!zrj17B7?wvgK`iuJ"
    "xg_Q6ZvYYYr3#qsdF^AdoKgF?M9S{xH3diHyEp-u*op4KbGmoYXEOTwclDDW-Akq&%sR{9E$wVpSt#~fR!i;x9ApuoUjWrEY0V+%"
    "q^}fb5#}tvC^bcwt>y%omW|tiD`p_~At+L51!$zD-Sy>L0z{f0T5$5+edz9h1=A<r9hqUC%lEtlxF4gps?WzEtYfy2n_(4f4Q*Hs"
    "_|Fi{t{;(^OBP++eu-BX5E%!2)eYdgYPrw;;~V^6l4z{iah@kb9);tO4(tTEPvHNt1)BKq4UYTk^lFDE#{$sGL5k-jaB_{XF9tg7"
    "(+dwBTm-}*C2>x15N$?-oQL`l>4Qa8!)6<;s{-Ru2a_!Ls3=h`WY|$Wy1?zoCyYxw!hN6Y`#cCx&yUuqu{o;stXnsEz2Q5}+3Qqm"
    "5?~(3bIbIQ9@u+k+ou*|H8(X<6s%xv;bohdZNs?#%@&cq(uXs*r%eMVk95G{?U-r+ZP-k;y5_S5qP@p9I8b-xR!mM$RX1zhZpAc$"
    "YGw9QP#<;grr5=ew{8(>-5AWYy;9zjiKTNx)-G6y3q9IRCLTSHp0>&YTa#>9czY_M1>Av(Q=UZmmQx+6+9R!*mQJgksw)4hrxK0|"
    "kLvSNMLXJ|k-4y0C-j6pnX3Th9l3aSWv3eas5nCTur29-y!u9FLM#ow@Aqb@Qn)yeq>8Lqne7gFlL79eiv52RudJ%GBWTX!brl|1"
    "zBk1#<@nDz>JQmx=Q(TKt_&k=HWqtoa(`<G;RB^oa~#XbYK-siaKr!YU#lSe?f=~GfB)P5WA`-~Ii-{1_P60)+MP~G;EX@O|B}=z"
    "z<6-`+y8|~F&O-Re*>>zKt4^#dgp_tdinDCfn4nCPm`%ZKxK}pQg<j&yd;hg$xKSh#u$FKJfUb+pjYqs@QRkiIi@ZF^3|0cgKroe"
    "D(-$5;6U~(4Ev*0huJhHeerWhIwLX{LIo$36!$G~HTY51gfF`W<84w(Nu+RMMLs>K!-rBV7>|98Qymy?EoVqD4(_8Z{-nU<XM@UH"
    "R~pY*LOvZsqa$ZIEUgv!Q#cid-tT=OgBv_wA6Ukw>&Z3~Wu2b^vp5^W1@t!rcXxv62Ye;c{3EUtClmGKl+6w1l!1O$l$4no8xG{4"
    "!g~4Tl)p%STL4`hp(TaPpK~bi;zpq10J=p$F3PF>v)BUy=MwK>4kpLwQu!l91cHnp%wjaC*AK>XL;j{mI;Ht};sx0QF1&$Lc3eSV"
    ";`*vO0S=V((s5aHd03uHb3jl8WDp82X_p_2bInVeXk9nyXw<Ms>4nC<(j2ymQ*jJk1Xx42yi2QXc$AMV_WPHr8g$?M+53?nU;~zk"
    "c3X7rm-<&MbQjWL09pFkn5Nbj<)w#==%~nxbk@-c9qIrPbShyVH4L)|7QF}<fEijv*0kS{r6)LFasxyJKVYlmM=*!F^5hr$ab7_2"
    "gg<*f@;WV$Vi=9kDKynt@>#6H9EvCkM6iWpBk)u^PXQ3@edyRnI2D0^+dYR4+h#@acn_`YT_mlv7#p@a2h6rMqMO)LgGRXYRM7xs"
    "S1(f#HQ<JT0mEZzd7>9UFE|Som0U&u9oH@?{DK1xB5$UILX@s60>q*Th(*cflWZqRsdh3NsTe8|u#MjD&(@kdP7SwmO;ThlZr?t3"
    "?NM^Hp5C-HwT>gleLM%8(9!#gss-C5ro{$UL+Ja{Ek-M;H(0O?wYsnGkQl<pZZ_RIdaCG=iJ{hXF9_4G+VnF!t3%XUE}1~k`X;L0"
    "D1C;lTqtn!l4Yp0vMbmMkUl_hiyqap5k@0d#<K{-lzb#V7k2Gj0XA~1<@HRT+E(waPtQi~vR*(#mTZoSM>9>gMTV6ZUnQ<1U=3}r"
    "qlb=+MxwrW^3f&JW>Pu55#yCi2fYe2+}-^>Q@a9=+O-kS9u;%KqO)=~a+#wkQz%<F?YhF%4kZ~ZwT=iThqSsxWIvlh>pKzqq?NCv"
    "AkFVPYz++Js|eMK^X{bY23jTk%(zloT?YOQEKz2HT8q2)TINu#q{L`9*v0ThP}v=|>a18{l{_;%?_?D$yZjY~a<NXv*>f6>R$pu{"
    "t<!F!a<~><o<INYe$fh~m|2oyPT+;{0TCt>zZ9BZ#>hbIMw~jh$Zx>8-&MP=kF;%Ef2h?zLDGb_rwx6gcygc=`J0V<q<mqJWu`if"
    "`EW^FVi6@p!7B955L7W~m4Q3te41b*fJGT_>N*!aYsGl_Vi-gwUsWo)4u}9R(g9%vYj&Te^XnK$*&Q-<k8Lw`u9$O%FG-j1S^z4D"
    "L;52DF)=QicVQ7}at;7mf#z6&hqzqMN{q19g@mEqN6lx82(yumgeN)VQUbtKNkL(~IlTfl0L5^S?}1<@felwYOF~GR_Wbr!TS61p"
    ">h#(~>OGduU5D{9<=_)yM+vXYEIDPaAdw>H&&|)KVyLKv8UddifG%aPfQ0iRXRsPTD%n&9BdboO^>;z%n-2$Er=?#`46iGbl{=XF"
    "LFs>$folMyp6>Et{cWLHyJPQ38pa9Eu(JE5p;>6|Z2f`wb$6rv!8Us~F?F8jq1$G+`!rNT<DBaUh9gisd(iQAhLYA4Rsx5Qt@|3{"
    "^e#xe_a+~omu7d9TbLV1G23gF0UoG<Y*n3~;g~%10UV})jCSYjBf{j0BT1QC`PVu#5hZE!Y#mo~<n5r2Wlu7XcPE{if$KiOsABd9"
    "l&<d?4<I_4e}+xh&0^tn0rQf6P?=E9NFJO`(aX~X-^aD+GYtS3$&b7~Ae&TRc*6&z&40Q@xU=ut+pEg~P=a-F+VjZlVfb_u7QKvX"
    "E&zsMu3+1Lf$d@|(D!i6A)U-aeL+5K%T(o>dkK+x52Uj0qbK#m0_Vs{-a;J8VE{FV=ki>s3>Gd9&a0%ng>Z_?ps{lESl!)yt7iA}"
    "Z6;<MUPYJ1c~;Jw=|;Y}k%m~rTIq(!+3OTgFS|aAJ2A(7RDjpEE~W*B3Q~LT-_fKN4CwNoa?0A>4DV}dt|a>}YNPmHiCfdR8`y)5"
    "kY$mm$mfs+oI?yehj_1wfDEfgox;tM?RgW~p=G%53?<P}e7Uz4r^Ghu(;V?Hf8C>dQFu}cW-m6s;B6ovX@6NLjkuksa{Fm`TbvYF"
    ">f&$XGEKi;4iAteRZR^-2%Od*om6VT{1IracpEQ=KTY{Ev}tL#M)A$OeK9;KAy_E5W4{qUtd(3f4p-^>j0?Z)U$Mx_=KOc!lbF>E"
    "y36_MZ(Kk@5j_KA>F3Uc;o(TdI$*h66*iwH<aE`0pE1><adMgj0xFr5?-!6xY0e&OWUUdVgXiG~xc+0l^XX8O`o3^$lMe+bOJ#I4"
    "seA}L72L|K6p~dA)rnx6<DDsU9z@2y{7w32L8km@lI#GWCg5@^9N9;kB02yn^=k*Ox?D|!gL-;h>lr-@TlDTxD}bthKx_yun+!zW"
    "d$je&_>vyxY^hv9UP*<3ZkE@K{B8>Kch@-`&-YU6hoH**jzL=O5<yId$+Fl)nv(2FilmAS&K{H2ONdfG+g^h|MdCPbdC`3cqvh?g"
    "7$QiQF%>Oo1uvq42yeP_)Pq~gW#uL++_bwczrp~xvdZ|Z=*(Bxa@z&z9VM4n21(D#0aa1>W;LD)r5>=DoUt;K+NW$qMr{<D)9ZCn"
    "X3se`bCbjZ#3BQ~eyg0RSN7>lY%i|V22dK<)aa$FrCQ>oW2x3sD{Hf>QxY*g@pdXvRcBYca$E*EP^{GRTp^KRv%b@H5m*_kRY&j3"
    "7bLY8>cb}nn*STItT|B~Aj%`}nU$e;`w#plxZfM9li>srYuB^Shhcn)vx62){JB(CSQ>$lS;7rXh#Vz7(8V`>Am?~Q)|4I9mYSEi"
    "+65~p=R}r7y-}(J+QD}B%7!$Jq~W~_q0X|w@9k3ANobpdGAT87*d0o5twzE(0!POD=VC5U#=01$*}&Dn;Sq>ybSQ<Q<)YffrHGe$"
    "Ea9rj1-_AT1C$2@IVTm8NS=;Dk0Ntz!8|WKXL4E*^YMnFq)HBw3`noaLum<16iOE+oor#yJJ;_byAI3-dQ#bKtVH3<vdC}~L2@Jh"
    "Om_>5#-!tpx2)G65NUG@`mUF5WacTQqk&fk3Ty?Q$l;@E`!S}p>y|kwed)zXiIU(%|LliBwi8)A&vCb)REKk+b3;ynhx!;Y43oyI"
    "V!X$`9=^#+wM3;odrjD9$`Zv(`80uXFe};voU#Wt!Fxh&>2MV>Z(gaAH{o~PrRcm6mvIhDGRLUIG<MvFMWvPi?t`a-{b)er&jzIb"
    "p7@4+u%8k0;lWLSD4~Qe0M9^Q#8<f>E)~il0oHLGlr)zi-E5x7-U`v1*a?AB`t~FQ-o4>8Os}<qL;3mOw4)?O!atGh1ffsR!0em6"
    "G|3@ENU5lTiLrARle_rXcjQ|~#0*OMtwJ0^x#tiMGIaNK@!yce29qGKE9_;@4YqAn#d-Eq9x9>1H&X=@GodfE^81(T<)Koll<>aL"
    "*FqeeA0nE+!FifP;f78-S_ktixD+b~UluLC6Z0JtyUq3`CtBdM+a@j<=v&iOPUA!zTA{Fai587>w8(Bj4z0`t^o~wDf76^qUDB1J"
    "PZEBc!JJy6z)#r{9><ijM0>@+iq0}hk2dc*_*@%dKJx+C7pFQ0fLpWBZMY9*t%B*>G@X#8;5no?cc`~Hlbvo-kRu&}oY3lZH6~G!"
    "4Gs?(fPy&z^1Ch+f0?4mY~wt9P5Pv9zQwS;V)}M}f6tG4>1<8(U7N^AJ5TC4=@1?Iig*tcyS8X-Srvf;?lU|I9b3?9?B^RMsLo|4"
    "BVVm_+b#DY;1{(_1-2<$CY=!mMC}AtT~yuIdAv8EAN|lhjX#ER5N-#Pi=?6apvZkUhc-U9T^S*0x>AeQ=jCRCJBx)%?2So&KvG1Z"
    "<g1Q-)!RPnMEX`gWG{fV!%mpnt(QeEJ8R1G0aE|Awr(H@qpn>!x%J||HLn%MeZpQ3s79tA{{BI-&FiZCkdwzDIx~gmxHO-V)Y4^5"
    "$KA^oR7V9`B6butcLE{FNz25e)fK#Y>{Qxy0b?16@$2Oe=1=TOKXpMUec{J0|I;3b<$sNp+>-pmANr;2ZtJgN<!m_c%W(R<_x&3W"
    "^w%2tQ#}ya>3=6sEgph`SSQ};po#&IyFL&7&t0fb=RzUO6ayLV05<WQradV{*#!0Vq@#IJFd(%ZmcY!-<3PnEWNu!ktqi<Bacmki"
    "kCJfvNJ60H4Fu!A-N$PISau#{%K5g{v-D1}5kCGs{K630dcKL$=M>8BVJn)GU(|sp#W*0$Sdj0gqBwz8LusTbe82x=x`5mNKWLtL"
    "kYwlkJ0!#6tII*<?Ojs5oMUu}vHI~zV7JSGQisahv@NG-Y7Tw3YebwvrZ<Ae9gdi2t-J_W-1`Z*-TxvyPXO-a`8)qqQEv_PPj%tJ"
    "8O>=$ekdtebErU8ze23tr;ivI0o^!N{$?H)wb%I4Ay=Nzhy0F8767!%K#CLP;)XD4(UZ>8%nwMb8~SM%D(k8PMmML*uZAcQqH5qO"
    "hT|aeT_t1(h+C9Qf21B~_=j1HmdmtzFL`QT)g`&XK4pL+!K<j$P`O!6On{wZIJ7Dq9Nc#j@~^Vgv_t(!jJN9{+R*|X9*aQ#*)}n%"
    "-Tb!PGf0R<1~i~r^l7}RgVQZU;cT6WcF2Y6=_+~=fXx$DUfBwQ1S7th8X*%x_-HjO4v~7K!~K!+M<g0BA0+v00?mtLBerP!4Y6Xv"
    "U>fz9{*9tvD%vOlxT#@OU{5dz^8#!?Nd~CA^lZ+%N|gJp(P!@9dT*Scl;8MS1$b}u)B(coGyY+BrN|bXzT#vGy_#)HJevfi(IK~t"
    "?9}B5v+#Qyt(cAX><3U>H?Do{oqZ!a1vs7{p0J2LliM&fE_?(l8<js0M_gI}JRlc}k`_>tEIx>Qg&wJC-_PV+<uoSh9*i(R3KRJP"
    "Pe}2eSMUY=>@y+Y{5rxw_uc#Q61+G$DZu1%RFYA=<`|P(UWpYbC-X~Rv!HO201X{~Tz7v>@ZyWDJlO&j2PBwpkkLOc5Qf|BNpU+;"
    "j_vNge8G%2S*Q0?wPlf2ImT2@DgqFKD~59_)28kP3YGvWa^q2a#;*8_$JnF~_@CLg^;*W8%Rb7e@ZFod^FPhTUUnS`6y~MmjSLWF"
    "!R>BsCv-lFOl2+Y6>f1LFEbkpPo_C=o}(z7W^IuAwa`n3tGK9u3S<=vRxY14rZAR;UZO3vi<^K~<TM8^S4U#YaVm8o`zG<Pzhi1M"
    "tX}NhvJ-ZK_iDjyu5-J}8lT7B7AMQ8_w@6IHERqb9;YCX0O2>&JdQMda>n7h)jtQW<-?_HG^ykbi{y>#?+~s}%bRE&Gx9v?#Md`l"
    "srf-j>@P}dk;n|KD$RGl-!4%V_dUKW-5;EMV%~HbJY5F&eQU@wl~^^Xxol&sdSHf9@aZyVz>MUo&Sml!4ZhO%nZGXk>$3mgWr!z0"
    "$E@V8mE9|Q^YYVWV25&)M&MF*sIy>xOe{%u)9<y}G5dadzseEm{@U<JF4YltVKXZ2u8{S-q5mvf2O>g%S$$%zX{>UETW~k1U#I9)"
    "?>V@%iOIib8e*!K!CpI8phQxrb|=Y_@kAS9zEgcXAFNO<2ulXTs!BuKiq0YdO=gZc>E=b1I!Xw>Q7)8pa}B7RLJ|@(HXTe9j1zx6"
    "A-_na5h&cJ&ndj5fGy3R@SOJm4FwfDnhFyC#7ji3UiM5TT)92If5L<#RTdm(-Qjldbnn3!#ZYdecQK)h0)l?Lgva`X`evMY<Wjds"
    "XQSwID=yW(?R*rUeQ_5SvRoP~oPBkB^57)}7$0C1vzE3%jB&t&-ZAT0|IYK!z=1k0l<Hm_7q52gU0zqSVt(eZ(VoP&xF1yZd5nth"
    "gR+<iM^!NrZsivfxn2eu58+aBqL~Ol)4+Miaj(lhaR=_x)JuQSo^7*<*WRQ={_BTU>E=JR{_^I#2apat!N{wngJ&A!{cq!rv}xPX"
    "?tNV7<;ji|d=(WVHd?=ndOmvf03HAE;%S3$d!W{^_{Op9t-qq`*;vPq(hl<U+Pi&HmyAlVT<5OPLb^30CE03H!jnRX_xnp$F_lPB"
    "NJvoP3@a4QVRxaG9b7O%Vwp>O{&`VNm0-Od83<K>1!TEs;dhE_^7i<OKMk;a_tli-WbNjT?JrpU&6l_8+^XTeeOd;w{+w+YXkc30"
    "9Q~xTffrL1-G>s@+6(qCL$s&f`s}CrtA4hJ>xvr1)tFW@;|wdaF4=VE<*X!12X-s*Df7xzD@`>FDC)<cDyk>F_xnQAPEw44{V}&b"
    "W#uydB|$B0a!x&OqWprTaAN+Z$wcB6ruHkpcr&a0N03n!KYe^{JBobcOylsW6}!CLLE1R&BjD~8FFEbr5R>lq8oS})`AbkKD_p`!"
    "6x(1p5wCoU1%B1&Qpx9xw{6kiYCAJ@X|%hMMd&GMI$!@*&PPwiVh_gsrT#}XZ1E1w<5D^qr?h(~k`6G6rib~H9=Q`F@WMrSpzD{-"
    "rVYNIyWphOAG*Xrxc>B07kbU;cVQhXkdiX^p-boUT}<{{o7Y_cw6kY1T&^#>_{w57HR@d=j+b2y%jowPTWZ*+ueyLUlHW-msPq1!"
    "OZN>Y<iG6VavjB-=^A+5#g%Q$L{}nwf88aVnzoNK_ucoh3xIjWeEVgx@v2K%G6ZG)M7Im@3~ig^AG&Z`$;7Ui*RQ*<@x4(LPMP!T"
    "E`aIRFCHScmtCZ@?XC1<M&<hxr~iMb%hS?({iXlwbxDS2MjcZn_s4Vrg2_eH78deup^WEO0ufVCaxcUsVGdNBVY=T6N#o}MFze-i"
    "`sQ=S^g6axE*VWf#n9RoxkRO2_{<_HvXT4C%YW<UY&dTY2;QD!ZT>tc_#JrjJ-><47HXlgxl=dKF_p3A%_FO?9V<_}dHZq9`rMB9"
    "u8awfPUUI;0$L$5y&5xjAD`_g<%OGEL7c9xv0EfTKiA2IU>eHV4w#6a3RB@qPC&2HP}`&74~j`&&^d#4KkF?M!M4OApU>}}%$P(!"
    "Ob7|*7NcC#^9f2W-Mriyr%!6MG$&87u!VfITh}2GQI0m{&1d`S&My|;Hq<L95x&0H1TAu*r5IuDq4Snj3L+tHjXb+MIg_XLkkl&!"
    "b$>ETlR}28`A<I+n^j;GY;B4aHtJm#+KdCAvi-$>w!|%O2*>S{kz@T{*eVMSY=8IbC<h3zuFZzZ!D$}UeA&}JZe3)7V^-F%2VBn>"
    "71dm~QHn6LWfsEEhysN;hm^DsGr6qC`59%uQI*h`Z;HAADA)=uVOe#Y7kh;hARsaV!xF0ov6+R+B9Nvrfs}Rb%hrU%vH`Und?k;;"
    "60`1^?VQNx5nc{}`AM%sJn61~P;?5<i@7Evr=9xua0}QslW%{U1y7;wmu5UZ?6&+<965wk0?@C|gy<8ozsv=oz~Ko{RWNFe%8cO-"
    "(tSeoaU6G~W<F~+N{E@8<}>58CchNY5UiyY1q|;7l_(WRy0ozzYaBr{?2#F8YYYyQYZ>65(9S&MtP3YjF$`yvK#1(6VW(7Z1n0)W"
    "k76a;j-qSx$%)N$xm8l33O-tQtbobCj#UE!Qc~3^xH21-SFDm=7p9;tZYG<d3}*Zo@;yM#wP(fJmC3=*dQxOVEQG==)BBDhLmiZS"
    "MDP1yn~srR=h}+o^O)v-FUaSH9J9c|=ol_<vG<XzK}Ro0*!D}%^@A(y$;Ed`ZcPkA5rK4KGdLQzwsqLs%}uzN2;~6yiO<_vxPP`k"
    "*2)YO7s3082F0g7*IMV3JM$U%^p}@`q^;`qbyZOg53O!Ep}K*I?Df^V-k-AdD7CtuY3Z2>L=aT<TVbi2UEZ$S%C>TnrLuC@bX#G{"
    "MBZ(3=m`(re)5M^tWxw3f?<QpL00eDD8wi#{MzbAYC>s3ag5Wymj9J6hvbCpssY_b*6FvaGX9>-LNQ+wL%Ql$Af2>QkYx1_BrKOh"
    "nYWeRwH|2qj(WS#_6t;_U{<2ks$b5i$2dl2-voe8?TCJ>VR+Sg$|%qVNUzI(#&i!JHnbU?35nG6?1NIep};JlcdZl33k`Nc9ybAt"
    ";L>U*tvJDI>F+OI^&=*|>Uf|76864SBixp$SW1QaE;d^=#bY6(_H+#w|Nr*BLrHZd%l2EiPz2@@AqlI8mGIscrrtcDaE14#u;2ca"
    "N=cb=P^ag1&+VQ=Oq_|nB~po$xpSMf*SgAEW_&3O`|h+SZ(6%>LRnTkUaTT;`0rTj`@FJ^Y-^oW7qw{Poe=_a5oz494`>{Dc0`Ds"
    "fvx6kColeq`aF3xT2wP{NO116R3v|Jj*Rc5%)+@`Coy9*W8aD7Eh|u^#mxnXZ{k@bg~}C^o`Q1<o~=TbfFQ7xlaIO`vMP38RQuoD"
    "w&F^Kiq-=Dig^@MIMSZlNXZmCTswwZU{T-^ID&8IBm|Mn-1O=u_Z_#8D@)pPLkSKL6|`!w_-nqFqiFVG2c`fw=r03igutNcreI^I"
    "^lMkmlz=U!Dqn(|lic{z<ZUJ9Df69i8fFhaf?-gvVk-huAXPWx9g`v@3;L<ta+BUAnd+ewg(%+&c0g$;+&9*&(^_B&piB+hA;WQ_"
    "<PL4@sHGp14`-tWW~hpTs6C2)_JBGHUJUfD1%D4CSee<SmOK{A5hGf@>)mQDN#h}>YK;M3NO!7>i1Ngzk!gw#>^vjb$xd+1Qo(6o"
    "Ec+PXV({;eq=T4J4&k?@T=6`)j}s!Fz;+|R-bS0=RBOZ9d;XbVTU}LuU3p2SyONjnda-Gyeu{OzP0ObFBm4a>vo|zmZ#*)46YWk4"
    "4QH{t3mN*u&~hykfg+MU5%(nA*b(*EQ7y71kX*>-W~^RIF#h!IHbMAS?AAikR-$ShUbcJ&wla5|mBg;Vyo=_SQ=|Q14RHH@)8hG+"
    "qz*vFpp3E^Z)}1!fARDMe9+!Z*7-7D*Lyy!rKp$|4H3zTk8;`Uy-!OXxMZ)_>i`y^$+mSNic>glBBpC=3~AKXKls=RE^S*{XxYWm"
    "HSWWgxWl$zRxB+cdD6&h0<L68S)q?NL(*ENr6PG6^}r@jgduVw$_!=dP?73zw0P!HmNphX#5X5l;Y*50i<CWVl9EUl$T9-zHc(f|"
    "Su#lY9<~O?6Vn45Yu}Yzpq?gBVJdHZ1k=BG<Q`!H^`gQuY5QQmAxv+%cR5=W8Y5ZXa`e$9=~A_}xF>0hPFK@e_*lTstt;U_Yd9&S"
    "SUO$bOPT`+O4}$RP<+-=vD<XO9h1Ie(C#+mFvJ|>NdQ<km{&J4UA&A-9Vi&;TP?oah9BUTkEf>6iSZ_GjorIAz%AGbh1*NAJnb%p"
    "ow8ku-v9%sJ@2O211St3|Le5=H9(whCg(>Ww%Z0XtK&G*n%%-c8+U`7k^cj6&o0o`#KW%sAe^xq-M-VFGvQ2Tc@2nmHW%v){R)}k"
    "M;`4#q;J6vysL(w;*sgXpt@_id|TPUxE8&bx2qfRSA1&Q{VdDNB0dBqj>!EiXaxc@Uo^FZlnUY8ic4yi7fZ97z>4mC9=t$w2_zz!"
    "TBH|PZiT1ehfjlV@&a7hw5SF@b(bIKcyYnUC87j~)e7K+q_kB`z(!JMnT4VdNi?r@CIK98ynELY62)v48k4{HVg2|c2*s`X7W{uM"
    "AJ7M#P^ZZn_4^4>60w6#aG$1Ee%JY6D{3lO;gu)_!zRRLKIjO96aHHVV+Q7Fmb~V>1qurSAF6y9$H1|1ffMR4@|V^vQz!`rHJ$Sj"
    "r(`83B>BkPb}o0v15!hlhi}MotILf_^YK}m$aI2K&VS+P%beBFEHr{CC+r8Q16fhdi=I0feH<4-3=3zYD~#bRWcw97&UHdT&e!_9"
    "U7ZLGzL>5r@A&zhDWCCRhU$3b`BZj4`N;Z^j}U!lF5ZHy$Q#MvZf)&smf0QFv35`;i|k1;6rR90?mE<B=J)9|WU<%pob93+aY=%3"
    "C9LsR`B0(0EV$A1-6qS<q6v9P{1-j;69rKh#HRMT?=sebS}?7_F6yg}M{Yb|%Z|EQY*U5LoOO&>oiaOWp>f@KQeiG7JX<-xWi&FR"
    "_KmAi!AZbVqmD+UrIkMWK2CAnH6#J^PI}N;MJ+rdP~Yn;YH?YZ9i7HoZ2WSUHD*aS*r7pjhk~A3zPtR7zg_>`PbQ@ObpPfbz{377"
    "dqRKJD~o_-6H*)Y^5W+8z4*bvN<@f7vGRk5;z;HKbG`M8{aBOt7_&SxTLK*OP@6AQ^P|SGvfL0`7wa0W0wB4YqmcZ%)hID{s<K|q"
    "(3=8eTWR*arJgFwO66oZhi&9ux<n&N24(8Fyi&63Msrj;#WHQ1qe&+JsOa>PtXC-cW_@<_iQy^vF0|d~Y^-7S6i+zZx@L<y*1xZ^"
    "2|45^dNjOo#S;dsO5;8qa1OraBPfGyY^}i}UCW>zvh8%;iq<e@*Wk{J-@~;t$`>;`8-)B-l+(@)hLbjqv(EJ+v8QXOz5ia*l>X6I"
    "*tlmZ!Drc`wg>E+@smZpovh{B>?&Z@(vxIf*%h!u!+<Wq12Yps8wV9>^=J0fZ5PP<Zbg46pD+p@0iuM$9{8lnALB^FQkG>qg~hM2"
    "-%Yj~4HO^mSHWk>SnGcNYyR5gbcJ9asSjjrd~Z}Zzttk8s{2wE-17mxMq|f)l2{9et*==%-Qv`nROKNV1dQdr7QQNgz(Upz5=3Gj"
    "hgzIWdX<1J0*2R+1s!`k2z0J`JA&pZ$d@Q6wW*Rx3N;j8%L3ILNcvRSed1h%vA4`hc+QM{k8R{+KHnAdhR#4mW>DH9Gg`r>DE&tH"
    "MEhGm-Z!YLJ?$vSLfEwmAiUDJ_DcQ7zV?rO$hYi>v1PrVR@I*peYgaKDm?xr$<w4&ROrb)B_w3&>OpRqNeSG~eCnd_Z{*Fa7?ct;"
    "4kb1i8Cr7f-%heUnGXwgXavwN0<A%k{L@K;|5FD?*@S1e*pF`4Eqh{*E;iYJ_N0;?Odm<u#oL`0g+IS)mo_@B1&?~{jwzz5LL}|H"
    "&|J66=5U1BGKO$$m2GDEe$GhfpzyxM{gP>26*Z~%N!9z_QY>vES+Q9F(6xf;d7|U@nBBx66h%I~zdm;+bX*Ohi<PZ>pUXDLJB0Kf"
    "pQlsUU)}o<->sPCQv#vIAQyWA(lT1EHeZO~;t4lEZ|>;Mi^U8Oa3F6VW7er+?G_)1kS5P!*$t1_Q7+Sd6S^dM+w5jMH9myryC`lV"
    "pOqCm?U(j<hS%YM-p$vi_r{%3lbsE5E75DG13QklInU*GD@@<{Z*VqzNtB^dw~+4@uom5MCrL1$;l`FvRbFrLHTVX#yT!hGef~s*"
    "Raq!`vhxTfIrpqML_dN1aW$WDmj+De>j=c2L-OO;*GE_e?+|_h5VoiiMf$$KMJqdi-B>`_KA>%cThA5$x_YFaK+M*e)H@F>fZ|tP"
    "=i!Z8O*^de%cs=EpFlcp=`zc=y2IrI$sf`io8<aYKG{$BV9v}PXg4hKZn1nBC5+dBRPKi08Sy6+dx<YV6%Z4c4q@=i;<g#;lL$Xy"
    "21fR(f5H)4u|Q#=B>V(-)^M%WHf;oTa<id1_n2mP2_=zgqn{9+SiZTLdJZX+ngxW5H5@Ynxjy-yFyWl1YJWt;z17(*zu<YONa*lg"
    "4bvsR(ECE(jQa^}GS?6AG*^JQ-J)7ZcIS;AB;R`w9YmfNQHd(w#ZzktOn0P9<~FYFQb^9;Bo-~0Vvd^+K~U_mV&2IiQuRTH{yKGC"
    "#7Y>M;z{mNropg?Wpj6bs(oA#>3(->`QFTAOayQ{GxU#7DT+DVLBCt+$KUV~d5~JWJ%0QR*o3}~{rnzK&Tbp5A`LU_k5%I&t-gnq"
    "-`I=yS#*d0)iZRhZ^=Sl<=gsv2k2)<YKg<jW9oHI@!WTw@1G9!7sG(6_)mE)53S(x>aWM@dPkdA<V}>k_24b?Ji5+$ZiDY|%-*kC"
    ">mH+Bm6QU9FaxC|9VD-`<k3=E0?PrOHirds@Vs0JJs4qKsk!4NUoIehg^u24ynK}{NC}kGw_MTgcyVz&*%BRAP5vy|!wnAzv9z@D"
    "R-a!iC`t>?)r&bp7$w%>^5nxAz)eUZL1n`LT$j|FG53g<NgrAba&>U|XW_c#PYD*$SK8g%gwDhP@e5!t0WA<h`qdeB=}g?qooJND"
    "zjImFHYZk<)4cXQXoc+l$>~+}GOLs(REkI+8!p~UAl%id_((MA<3WEzJKz(zVnL^^;Py5BS{HM^!Cj*KZK3!{YtHUqsI-%upK=JV"
    "Osb(&oT)xYZwv1jR44NR6+7Ny&_g(8C|idQe3<FxqB`DuQ8saR->RRuQsC0aZ{riurp#%M&zW`jOV$Ck$Km6={I5vufzKIqF9YHu"
    "ybsUQ%6_Yvj0pmql~a{n@+PIyffEZ+4_WI}?Z-PaZs|25f4a(@vvrMapOP#n`zGEOu=}h=R*kocaSQYGJ9sukmWNhLGcuij-o?Of"
    "v$#N>lQ-K4YAX+Cx)I-`d1!rB2Ew?di_`wJmnWB5_XiiiUSofi4qYA*yQKskW`NzNQ|!aD>!6E8_XTIt734U<ORu~S1-w8$Y!r@o"
    "1jO*=uhL<1MMZuQ(C3|fX_2%eQW_}7pqiv~Tu3C@Ldj5jl0b}StE}&9Pm+?D+L^bflN<`d_gvh`Gp6ZHvL{H%f_8`UwR_N*<hv_V"
    "i;qQm0=6^o@6$u&BvqL#e_9a0R7_H#8+A*{+t;Zt{bi9o<4Gd<B&)6&bIt&*W{cn($LB-+CrQ3_5&Fv|_;K1#k^~(?H(BCH=XF!_"
    "hD5H@DL;AL*lQGZg|%Nd>X88O8a_*>vnGk?swUdEwIQuPNy2rUDcS(^CW+<9p?HwaB;%Nk5V|C_Cy5D5=Q_o<-Xv+jnR`&M3M*bW"
    "=RZ8|IH$mBZhvWlfEBO<wT+i1DC8bEK+=iQx$fh<=VGYXHRYsDd&%vM0`uvH(jSyY8?diXip09%*rnfd6y}$9vRNOh$^h=msHJK~"
    "j(QjJ49+|7n%$aHKND4{uYyLU>~u5M+mYTOF%UVTB@W2wcSBe^*}(!O(!JB`m-m3KL+)E}{nf$q<$|ydyzVUaszeD@)}8Oog4boG"
    "QVpxofo5ie>zp^q)ulBO_yE1dUstBZ6|=2q5nr6)br@R~YCn-}kG5|ZS@NPr;u6j^_5JHy)>BpCP&Gc-(wu$kON3y(FNIm5rC;(x"
    "pt-`-pVz$(;HgBM@pKW_y$;yw`VYp#sWN8SC(os1ryW1|y`uc~%jcJfIS)U1A27f3<o!yncl7vdy^y>rK!95hMCIA~t93=JV&U*)"
    "Jv;4r?ndu?$YVe%BAFulj`uE-kwyglK-A`=*l*;x;f>z1Rgu9OaVcaMN94@r_=ZC%`3k0y>!9{5&K_(Zo^jnc;(;mvUW)F)H?#ZH"
    "<*T|%t<2-Jjuh90A0zUlwQ7rn#G5B<U05gnd1<^r$QfWgW59a)1n1MO?|kOpZn;bDQz5iNJ$F9G{k+L0dh##Lf232I;$<ww!T0!_"
    "yN~`7DLkL_hr_Ptm%vjkc^ineliWwKtmE5?7RcvM2~Fd<<k<7v7xj2qqX?PFbSlq$N1=sAphbMU#hxAh1S?23@WA!cV*A9Sz*^b_"
    "Wo~^pg>YJO3NWqibn(qBk|yd+mjD8#BDCwX$vm4bffxTF->B|%2@2~Pgj|NY(<OXGDG(IoOLV78loBWLw?VL>{&WdU4%Hc*o1RTK"
    "ieWfl!>aCdsW*p|2KLa;rwdwX%rcHl-RY7TRAVuX5#}e;l@fK_1ADO;oQ}XwcyF2IWc6&iWJwWWKXKW~vy>E%6rXOjC`!8pSEim*"
    "f4c5%mz3;fLC-S0dl?f$qb!X%NBgWV4H>Y1-g@OnhHSIN(|wxG@wRQW-KT~Nn~R-4<T>0p%;7?FOgzg4;Qs^)*7NvPc)yLFel*lM"
    "etNdnIkO6eda=<+TPpeY8w$5_8bgu&;VpGYygxryVhK;x{!brD{*T^J^5gdXzcbXo`Un2%P(ONu>d(JsDEIv?;ANf-wJV20_J8$I"
    "zQge~>eBxM%ka~ofEi1Oy=0&zo&KpA+m(ub>x(<YYyDT36xQTje)uRckcfH_Jv}AArpUi|$4(n1pBp4$jL35@1I69^f6;`r9Ah*g"
    "Q11q<X5Z>1EltSTV{r~D%?Xh#7sJIhGk$17^>`<5*PM|2AMFV#l+!gQq@XwX$0zhZ^n`x$%AQ!E!9cGftG|Z+eJ7;pB*_#vb(}6{"
    "{ex(f*SwZ{SxFf5@+m`?R?0AcA9lkbN2xpt%r-Wnp6Tw+8oz75sYezT#r=YB<&>fV)xt=Klu5=%6$5>}J9<q4PmpRaTfS4y+%C4i"
    "2Nk8NFcJmG(Q_=5LK)+OBQ7ZHDt<^_v9brG{uQmT(x6r(Er99Vi;Lcf26e`R0U_i{_(m!a0XYKc8GcY#x`|OiYkVf}#Fo#+IuV6p"
    "Ff?|kb3^3h3l8edSuHPeO+_NI6LDt3bJiiL_|=3M_kb~_84<PfgRI??tRmiU%>CnSR(tx=)Iip-|AW+`a!{3u_RsQ*n650}6d!!U"
    "R&hK^9VS`@R`9xukV;#4rkBvOL5&#AwVF5ulRqqqa_9Wp->Pr{5O@g(HB?Zc0ti<g^#_$Gqcve5vO$Z^ujEb0Wh2O+=AZ;&6L%DQ"
    "S1uL#p!hc3bV5%D<@WwPFVF#GzJ|FcgMuv{3oHeq?Erf{xd*%aHaUJD7nFm7M3szOLJ>TU=1}iWs^D+FGe?ytmib(#H9)VvLYd6m"
    "!ZG`N7Mw8Txc{ilzHx(`0{CG{2z!0H{vtfSi-Dm*dE@A=ve9uHD1*kqVfn@3c`mdk`Kp$xjQ!L#mvldQ#=4hL$nW9*b;Cd5EdO{J"
    "g3JE-ONRgbYJU&^&lz6Jqy7sm=C2xLa15kHZD>I=PwyC5?#dHY9BDR9^lqq`hSq#inu&1Dckp}A|ENK=Vo>cRm6~WQ-*2#dGjRDj"
    "TmloLi<AOO&G41}{0sgnC8ESXMAb3N@4x>3>+iq9zitB3U)9aWlwE{sY_C@}o<!m}*f!M}3WS;3WFP`FT}e<Pu*=PUE0UR@`Q5F8"
    "NzZ3?>8}T%>bt;XoYMB|2>mrkRh-^(C2xk9uI^_wbVPrZmxek($CcIo>xRU`*!l;Nx)33{+^sC$s)I<a@{lLbvN&SoRjfuhFB#Q="
    "tnYc?T9#;(UmX60-^2huCFUXY8NBkF;-DRt1^mKaKd2b7$)h3C_Io42pVW>#XY=@$od@ziDo8n(4EL^*ho6<E;IF)@X>v4&hrd!c"
    "TdWu!{>sVx;P^>74gSjhCG(@gnyC*MeJ`menJsMixByOwwcl<(7+z$lixNxQ^y}s9We5BZhIiB~(={&m`eODn&L2HmS~NWO=O~ub"
    "1HjPY^Jh<uTC@bq@J3(1+5zb65p%Zh<m*bQ0c*PMzSWsm>)u&PAuZZA=ozs-U-vPKr6`hTY)z}z+iH(-N#$Lk-m7gz&9I*k3SZgM"
    "i(N}MW5}*v#4hG1MgfomO6XtL>w+?gufNQ9EBM@Ea%W4y_~Td&mLwP6$IoIl;RfIR$0jb1)pB@=_vJAle*T(Eep=c8eaY`j{_`#="
    "6;0oNr%PTUJJ|MLa|tjzc~B{!|Kxj|U9iU)iG_$hv`LFSk5Cd3#~fZ|&j+s_p~6~k8W%;|p6Zr6TBD<t@+yBt%(ew=18ZFPGS>d?"
    "s;YeHhr|TH?6oU(JND{(v~RLjVRr*3L1A+p>AT!5^M{T|CAz#SSYNW8#v8rTyCn%~=<u(RX!{-4YKqP7qeHxNXldRu*Xg))5UU05"
    "WzP|dqUx4JG7uL6xhx&QyxxX+VjW@CMb$0IGQxM_bVSM1^yZq5^ZK_WJPolyZG%Z-h5-_K_Ux8~J)83$g}f%UNeO3FcC^gZZHvj|"
    "$t?-0t`vwNNbBmB4UEmtZ;8vZRO7I0yFKPkfOi1NAZy){pa3oU3TrZRChw()C1`QJxFv=p-|~{o<eqaC+=th<<Zj{G1(C1ovKCie"
    "sE+mGmYDD-dnVgg<EO~;@#>ZYm5qx9%|$Qn-?=*iF89?f2_8iavEr8E`)VR^dc3|RK^B^*F_~NAE%Q%ri8o^JSShLh`j(v6i*0-N"
    "I!XQbmV_r#lxV#Uzj8}Vz7`8besW8~Jr$*PqLE*^r6>i&;LYPdx}_$T<43pD#EU3y2_USPsh_5`gk4t}VWsjU(IPh?3d^nPyUN4s"
    "7j6lT(E>O|33!YONgUbP!l>ygJPw==()aC<N%^pOC0&?-nhlVxtt<4NBjdfH{%rUxZ^jS{{lQ1w_9Z0%YaOrP#5S1P{HCgg<^WnF"
    "4?B~{1gN%*h5noQ`S3^#<%h#_&!GHE!`}+EQ~1^Jt8N#4qdm$EhtG%iRKKYPvZjJEs_yX9UClDO<wfzn&20aCcz2XGWpO1dcRurU"
    "_$1-(r7`)%rS0?6{$zOHce2#DXTqw|r{3_m)C~A%;3A$6&(l$1%p84xdiiX4K<HCoV#wt4T^&z`=iEC>d>`veB=2v}hvz;Id<!Qd"
    ";o8&TfrK@U>D+9Zu2%Qi@Ib~b)0Oh#%;d%J+)tMCnZ6sJ56{ggewObA@3Y~#PrwkwvtuuYCkWP@IypXmJUl^k@4qrU_X~(X^B0Ea"
    "thTwZwabQ=x&4LNNKS5v6q1DD6&6#aga{;*e?B~TrXN72KpY+%14Rr7>(KzhW~$~(b{y%a$)!J(U;2<zg!1!YFRB_>GbvUpE4#y!"
    "jCg=&Y_OrVi~`a1E*^4QUo_FLTHfEyzJT!G64N}M|D1SILc9=<mPJeMv?L_kg;9o1uj?3mct`&@CP{ygNVDWa(r9}iK4k?VE+8U-"
    ")WR!s!wC5KCKCNCqfGx|I*+iO(6yGr0$RmGl)Ep4#hiM}aVMd{D8|McHR&#rXW=5MBjF8a0xDfllmnFn77MG?nMha$qP1J73lYwb"
    "ycnHqEDIuckdy%AL_xw%cu0hIbebr25@I24wo(%Xdpk&Z=O{y<rqoJw-lY@*Fx0EIc_hKaxiPN*v&jA3F-6(Pww!uo#Ad`K-DX2X"
    "TrabD{aGD>p@_0G7x>}RIAKto!hGp?`kXVk67|Banlq;S3FNeV>7ICYt_p@{YXj(WIzoXbt8TnmVXKaCoh65mu0C1Mkd$X7{RC$I"
    "WT!wOV$%H!dl1(qI!===$*Chz=HwGoVDz(A!H0@FQ(~>md5LM+4T6ZB#a+8~GYQ5zE5G;6CSk!Pc6Ei1_l+O*&uty}d`8!C4J&%r"
    "$E|-J4V%cDF~1F@PL?QG?E`tawggPP^9LQJ+lRrveiV$)P$#HnT*&Jt>t$7hx4UL>gxp-4SfM7dbEUL1jbsh$tp>b2E6qBK%hKsd"
    "EI{wNNlQU!hR;FlgG0TF5Tezt=ne&PZ-Qr;oq_eQS^fD!j-h^UI>>?ud?wi*dC-{^(zg>zR9ZuUP2k5-ei}o$Nm`6Jw}GP0V{c$$"
    "TtK{MqI!cZa~*qw@yCjJg^XRzL$C0#n{4VC$d)qMJLQJq2bK6=Pq_ac>W4#Vw_+)eDNV}|y}2E~J`^xxWtpdnA?yCvd#azm<f*QG"
    "-~QmwJ=OPb^Upoid$aiqo+@+t1y7apMt<(8a(>P)c&eFS@l;QL4^Or5E1s(F7d%xu{41X7;TJqrf+mvm@$F}xYW-7Sx&Mi$3V;gT"
    "N9aeM>g+J(*0XK(6Hir;+t}WJ;Hh5E7yeixJwMok2+e?s40@hw3&W}TDMRO(ry7%GJY(yjzNZ==OcY`Od&pz2wsi-fm#Pv2@ZRLP"
    "N?x@lRo3lXjF%^zmmMCx2f0lgTlT=3Ouxvo6P~xME?KZT*<A%slG$ntwyCa$bxC_B6?4D-Mv3Qj7fBR}7n&fM)%R`t(~AjD`!WCV"
    "#RTc9!s_NvE(Qe?(`LPGU&?PM=_sw>e6#Ln<P2`BKjflqGGX%<lwaXhJQb&Z6hnY2z-)KMaXoTWKe<aplBg@W+Z!LOPu&y;qR$F+"
    "UE}bx763A#O}VY<Be4dB@BO3+!5!>Mc~R2~uPS~qiO8!@5Ba=f0g0JoI>6e~B_*rN_FqkR@+I2jrE&gzx(J&a8Tp*vC)1@i;-K5x"
    "Gya!eG`%aE9gvsL@9w&_`QMcMwY&UG*Js6h>zT+<W9RFI9*4?Phq>w<hLVy<m%2ize7Z#m>9`Glyl}C}p+uyv)EZVlT};P(!H_Tf"
    "`yAO3VCh-n{{4J0WZG|wi>&_kWHF#-;jklnaz0(VGX%)Mi)Pwuw~O#Cm=mwLcFC;tK3LDI0LERGq%LWbjv*6azSN-+!@~pTqM{Fw"
    "MDq5$R&%d1spyiNa3}Ex(y;yl=C}&XF$LAleDWOpYCvagrY>o!S4_5~kBUxbDSSoyx+xWFZ9cs$#lD(-9<CnSw?}<VHO1?rOahbF"
    "5FCPJYR=jD!F``Qg%4Kz5{M~c??5fVjr>dA)WS<#Ru3SfWR&Moc7Ff*hL^-UVbG;Ox3zpTcuC&D0@s;V$xcz(aspl=6iAu8R&koY"
    "M5J<MXU^$3&T5^AE}MA;lWgYBGLX|eHFrM$RpQi+XV!O{S>I2DkNq<|%Z4qhkhb56{_z+Mn2MG2!&TCz>8gK=l~b3qs(0GD#ljQW"
    "MCYX9A4_ua3Hw44_wZJmJPC<65#%O~z(F!p9l6J!qOUl09O<15IJ{b^LIBF<$_dgsQW-(ZtvOe=Qks<3bH?I0zeLjHa{$zpB5q8I"
    "J^)?eFZuGlg_Ng-NGj-Y@s|YF^Q}_%_TpYexwCFdANfmeG}%{Bc#r~R2@p!-FUhx)id7=6p}Fe-FDYyzHJl%T5}6!g#X?ZH1W=&("
    "KD~QaVn~{+_Lv`LD~#20aD*<=uw6H}<jIe>pw=6_X8MJW%mWUNR^Rlz()PJCBgd-Wvm)*hV3=w!b4*~m1cHqBi%#|^QCty;)(@_`"
    "xrX;2U00Z!Tk@_>P3+EU;NBRxN$xRIWLo>m@Z!m1=MXLi&yk-bc0y?4h}?4roFv|6Dru9fDCy>;15EP0ORf&|^GPlomzvTq(VXN@"
    "kVpDmGFp@TISNYa^LvuNC;4wUNsvKNWqi|PqdGl&-Koj9H$9Csa>b`{829BF>vu6@4a}!k*L-5K@yJ&P|1_7KsG2E3VgMsNcU<n-"
    "JGg4lDj*OKCDVppn1FLZO1+b;LF>UCLOlbP7DwS9kmgi<BORJ}il14R5OuSuPht3+r>7p?Q}EnepRKTz#mXr45oE8>BSZE7p7`&H"
    ">rUJ&;~OI-LMv9Y-}C&@4Py<?Wy-#U0VvSZP}PKh@B}6!j_F!xAjSx<X>lWB%TEayE(Hv<hM`K6w?gF|gP<a}SpzFD2X&$mo^&i*"
    "8C_Do;a8$2ODj0*Vxz;>u58RDgEw-Ux9ukAfq8=2!w4ey_JwQNiKm&Xj)B!&GvSDAL41=p^fpYFf$SyjoSmxl<h*@iW|dDS)T+I;"
    "a~Atx`i@=deq+WxWxzm2iS$7;rj0SdFO7G+In2Ksq(Vt+_staa$oo!(`G_^vx`)pD$zGcFhYEZjFz<B@wM8gA`-GEOI{$WT`JZ<&"
    "Uz+H+`yN;mal8{pm4Jk6<@~ar^UbyBH}8bF!j;Y|n|OJM5mZd#eP?&KB&Z`LCT~j2v@2%nhp_BErqxn)D^<!{O{R*sr_;8vN1Oi>"
    "rgi4BUUtLTrl%2Tly~rec^Ma)@J-HQfCI5E8<})V$0aMT5Vdo+Tr(`c8-+;%LCOZ<mW#1c8k+mqFtqa*U9pLI*iYm2-RD(2ArdKt"
    "wR^3O0A8jOUgDTC1(lusAea#*?sM6M4WC`@^YYy+L^e#jEi`9k@>#fjW480$BUAU5!s^eExc<bBmPN`Q(pHFclNC|!Y8~f$QDSZ1"
    "sMXaefOJbzvKVA`fR=$qCP6S<5(meQ;S~`$e`@B?s}QB6b~yH%ES4_TTWU_%^hzsJ^k&MB03nA3t6V@NxODLiB443&y`--Sisj+r"
    "1J^?UGU@r#NcRCG-hk{-UEc%FcM&5I`>OE8ZqJDN@m2kZT#4cjg^lHvq$}aBNrePY^<^1rF8IOuLFc6mEkOybAyNP1b<K+uOe8t`"
    "T514E8nA&B+HE(<+ikTnBa5FS*?2vzR2bs+hy<KlX%rKdXn>@k3b-|5js{+)xTyz7cPViIq>71A(>n1Y8awUTK_`ch3}>SO+}x+5"
    "qyP+wd05<V0V^_?W}Gl?K~NX_IaXO=umf{^56^~B%HG8?T-#&r*hfb@MhuJcn>d(Gp}dq0-!j97SaRa|eT99EyEPbQV8`G;3-Gh!"
    ")Xv_E2tVDlFwzIaE3C*pa<;eB*M_Db4qP%Q%Wux+(p&YJZdp?vBQ?fob$ks<*Z@Fr{OE6aX(h)8P*DXi)i*4iDACm#YJmmB3t4Q%"
    "8jFqqAaV{5h-vxS9_Tnx>|LPyB~#5?Ht;T0BiM)7Lq)A_IXf*o=c%z&4-s_aiKy#QS)}|S)K-y3_I=a17i8J|tzQHvu17HOemQ5V"
    "+@49L#omwg1agp!SldiRG?Q8%1aw2*;siF~7>AQg5^Iy}4^;n_KZc!3gUs#72i5_}P<tOgNz8Y0H@OqkxotH?4N=@QBEcV?_kX{R"
    "m-!9r3ft0EIKbvyYIJ&qM`5I4q@<hx>nGchHhIf0?BMVtC8!l^Ba4MT=c%Qq>S)0^l=La-0O2D_K|!ON3L~(Rg`no!97s-Q)n$@~"
    "2=ZA?Y+!i{uZN5eNQ9(m`W)errr`vRf?$ynCvG>=17RJc&3(ZHWh*!CLCk!bM=0)nSj+XZvEYQE1rRx-ML_q*32H~HKN$F=ZDg*9"
    "t|pC+THphA^-hUT*<N)^hY*$4*~ALZb$~Tu0yK<>?&5Xi#6Q@KDPpeu{YXyoAQ+s>hq`ymI+XRY57y@?@7~GHi*>A&p!We8FvtaF"
    "^UW<-K-Lc}?QjzZ+Wr1T@B81<BozneK&5}H`SFRt@T@DR7obE3Wj?k&^B@Fi5C8RxJ!$#wVVm(3e3D+|js!4C6_QY3P-8k8{y-DP"
    "aRi2jK{-Wb_Z8YA;GfpHH{5C@-QcT}_rDfoF`A-Fi^|KAb75G60i<Js$Y0Kzz<U4~_CmKUMFZM~PE4LY@$rrFehu#U-YHCF10Cr%"
    "?{+GdKug|=I(I-~92Ongc87ZcxD8RyXM>SjA%r`L66Wc?J_cnGE)wYXG$gs_SRe$jEjwqdo!J2u+M{}FC%@4l#<|A~NPi4<!gnmv"
    "V^8j&G41X2-ZLNC7mtUM)nM6RsC0U=KAqhRUaU=Q9qbd}73@?O@WRgt_=)tQEQU3kQvU^B%#-kmJv__Z<oU%p|B@9$iA>~qF1>|P"
    "2DdDke74nFc^oOIBErW%Am^RJwDjCx45<gn<BV4=jZ0ciLTT+9e&69Sao%4KBWAg{twoJT3{Kxo9hiLU<Aojs-ONxO`W&eP5=qnp"
    "(n%P%NrgqMaZb0?sE@cEckD#LD@YK<dlAo**gKLEG@~p!gKd?-mWu0S|4?WfN{;DVDXYLvcA^>C;_;W$8r&;<O@hdz3}OOs-RGw!"
    "X8@xGPg#T7`Fanp!!jH81~2Az&$seouen^rFD84R;9@NbXu1f@aSPIl328N_PI!iV0}>M~FyHCqR=2!Tk9Uf~#p!uvt6y2cvX^}E"
    "$C*c<UKNQUP=PfSLIoJ01O6bPjo007;qjug70F#)tAt>)Ttka!cec5ZGTY6D-!CW#*Jd1`PN7@&7Qnvi{3<)eARx1qe3UY`I2U=D"
    "IxZFHVrj(PE=>vPkM*1K2V%-K-g1Ta|3AA_E2hHAIk#Skr*8~*#&`d*GHUEd%+2E45rF5u#X9mZzhRvbnN9l4x6|e*S^?{bTA_s+"
    "N~Z}sA_sKtsFfds*q-Z@728q#HdDtJsA;2?srv+P#-po;o?gnKhJ(fGlZ}3IVrHpH&QPH9Ea%Ze!XKNbb{pfg!fF#*N78!oC0tAf"
    "&QAt)PO9Rdv&gfXlkvvyN$N}zM9*qfE2BDgz{IXGG>=A%K~}V?9$%l{$6Rt}KOmZr#M(Xa)P^n&$A6x^*7ocEd??Y0#Zx(Hqv(ok"
    "xzh{`#d*+u*>%)S!mzQoO#5wB)flRdcwBGv-8<GAikxm1Vsp*93#=8nRt@C}ZBV-g<f2l4><GMib6rhW&B%w?`ovV}s-fdK6&+b*"
    "qqK>62@>lS?l4Y9Q#LA7utmiJ*y5tyML|YV5)C%%)Uz>Ilc&GBaQQXE`ghMkwCtI#cJ%447PZrN_@|FifLzYKucFpPAY&5|*`X|q"
    "_U=Om^p4iCq2vb!nw&3^C!=P-h`O`WTc37VkJ3+ttw|>jPjznSZopkhYUMYuWs3nW6*Y*lXjlqcRf9*<I08v~mw$~g(&^n-R2H;="
    "`Z!}hd}7O%?iu=8LwQfhwj`QqRXfl8P=W60wRX+A7TO2AFRuIHP{54+Unr&E{*(Tb<eWfSg`GKELgpnNjKy3_nFeTOsp#=S13=ou"
    "*c&s(an7Jxho_DZ>)h`F{xb*o*+MFV_4r@^#VttE1Jgu6n#S|zA0QJrQzq2l0jbE+Q6w<ejKWWV8GmIy5uTEYBqgk(Fbe<E&9`j<"
    "T2nlfP1&qhS^AUT$vo30qc}*ToG0IGpFg@C{1C}}1Ud6cf67`=og2`T$k2+~Bab=<#Z8=jj>oa(2gir(tmV1OmF60Tx9d;xiU&dY"
    "&0}=Sec5HnLe~*^D74~mh0)P$ovq^nlSTTzzhx_3S;E7e0@(suk${B}lL949=5rn!UW9`K7{V&$6@q}FRBv5wVco#a6jOWLQq@~U"
    "8QT?h9{F1!VR+RrPi$DXsK;lpCT<DGUDl@QvF1QKk=$`0VN$AEbXT#19#oCrZ}Hk)_7=QVF6`XyI$8l)!Mt){*;OD}IK4%UZP{D!"
    "+PNpbt-OIv@&BNab|NE<SKGLMN{{Xl542rft1RxGhr8$rLI+b0!YZA|!!F_5UAm%gdFtZf>+b>nLkIZfg#^}P8#cDO1l4hpQjkQD"
    "H188#P4iAnFIIG3%SRh<=3IJCGjT)ZsP5aTs-;025la3-`=3SQ5(jU4F>inHZB`_{%|hCA^JW4t$_wD!RrshEA!oZfJP4{BhFRH2"
    "^6o-L>d^L$O#WNWe~0emN39x9aYOYGRnZ3a|EAcGXfVkGga!pS&LUq0obyG{Ym5wz@l(b7&E0&<@XqX*Z<6-AFKq?<qst>19h`-0"
    "@j1d>b?s77A5qsMNa~yH;7xXbWuds!*5&(?`~R*#|M*dp$Y1skm_rxN!TF~btR&x`e+X5yMO7#qLmk`gQamT2iY%KE@l#|=(Sz8}"
    "b~nvVFBcP{y6E>u^Oi1|#em6`Xvl;^NDv7SdoY<#Fd3fqoO>W%AT9=$c63%{!U4+G^zB@c55w-eX?EHt&vOvnkRgMeV4(F`l~%}q"
    "&APIr0~;PQH+Rj)THnPq0b8<Q`HOtyTl8)U2a&dW-+DvS;7dHhkgkUS74S|5S#cU&{A8E<oJ8Jb)dvU#gAk7mXmaLqcab_c>9S4+"
    "sV9b!vn_gRt&jO(RBihT8@xf38Ve=K#K9FeXssCm+~TCWdg+t1aIR8)SWpcZj;%R9jd>DWLP>qYRZ<!7QkMdE$&MAmO=dG*Dw5m$"
    "G!Q+A=vI(X`7}l{6rG4x#HV4-Nl9>6(DXE$Y#5&gq5@gRSI%4-7Y~L{1K?j|&%ozaJPo%mA2ng=`rdhlFGrBxVUy0XSdH0wzhvQm"
    "6ktgfW3t)3TRZiow^_NZEDV<F2R{&OpdPF%kf_U6H1sgk-f1n6zvdF~O5^|0m$;jgV=!o%hZfz_!Ju);_pD$`9>w*vDyc7_<TOj{"
    "UCif6m+YupsPdN0q%&=iHOLck#$}hVZ9!;z+!G3C`TC+HyMz&wT$DxPm$~0$m!K}?ic2Du%gHa1ObUf|QbzWR+ES*FlJ*`GkzIoL"
    "A;=I)4azR@95eu4XPtM16z|!H-X*A18Ge1E@7L2E>iuZR{4ycENB1QImc4iZS)JD?N%pNGUFBkcKt%n;;J$|{2R50CtQq0Z^1R(*"
    "vOTR_m=B)pUcT+WXKS`3p$vuUtI{&KoAXmB<uP=Yt54yq1BR&&PIj+wvb)5ST}UgJ7M12S(*O9*Uc#dbp5`N~Ddn;4ADt&50d{C|"
    "XmtJ4d{%NTvi7mzuTjt4ik|wJv-sD@U8><pBn$n#@K^Vnh-6!wQZj%D_g9x|DRlDYbDt=_bOzeBS_spum$wY8%#Dka$gyGxL=Kn#"
    "c=v3F#P#DUJV)<GQ(2z`AQYh=$Ze}C-2jYJ%Vpejp8S=MNPb~tj3NMo(8yCD5RL1!Y*j^LF=wR+@a^u2Z;3z2_XTP}0;(n?cnja+"
    "=37{@c$F9mazvyxHxtb)wXsSam&^8tH4xzaror+n7EPtCuIeqbw8F&|>#g!v#maG<w|7#+R-0MbU%ep@?IzJnaTUrLYc@O@Ome4+"
    "|K63B`2ahAX$_`nnLEax{4=YD79lCS{c@lwS13RJ2f9@}#Jj1hd`LKbuIjT1@spye&nE;v)qn1U5_Na?G44E?g`)4#c^uReauqNV"
    "t9)XsF`?K^@#;ZVt1g=miD=@D(OJ^i>OP!bZTW<xQ5fM&VIIYld_p7unJ@W9EO7z3SBeQ0eUWZZ0f+|humd(B#D{<|6ZBWfiBAYo"
    "@-5R132SteO(-Y%rC5q{D4!6<d5=0|kf+U02$S=0?PhJwSLUjRhbjnwat-;VHVsAtAqywuL7X1|Vhb-sGk{Ns&!s|8ZlodPi9Jc*"
    "5r0DNkxfOzh#GB#SEeMz<+B9JHMCkzAo#BPUG$}7Z(3SInB$d&uM7k!NyVZDN)T{Xi`*l)AKE;gmTFOdk@8@RX~<Id20pD#w%+d@"
    "5dpnD;B>p(kC8Ip<MMu<PF4exW6^-UGVss&1DLQOIH`TYN$r-O)QRdaUkbGi`Bq@DBl977^N$q+Tmm%UXXV&xNrl>i>ZD$G#}e>y"
    "Cj`^S$D6Cu$ij-AjqaW~gH8HqIRZkw$I1bgp4j(M*pPzHRj7~P>&Z>)bU|D`5+>Pw2qI|X*lkF`i<>@2J1qn50MVveR6xDB3%7?@"
    "Qxv*>YoS|5tS!$i5oHt`4H(_e$faH8ryO%D0LC5YUefNzKAC428*II3R$<>lbwf*^05=g68$F^sKL%{ghAtsfVNlwO5y2*a_jo1p"
    "^s)VU_`CsNJVc~p`ln9sDshX_Uq-@B+yrP?#@Z9|@l?gQ=e$=Qe?>aQ$}Vg8bROQWvD-Mm$66SDpDv^7xxAmyA>CN@D|pa-OXaL`"
    "?<de(*L~)8cTbb`L4=~O(m6f?bub#9<D~o?Cv(kpY|u6=gS63ZUj#&88DX-01jAE2eG9v}Nk&ClB($85Mdz7iV)kKb!u?_b?y3Dc"
    "UZZ$gO30%F%4K{jIW=#%uXr(tik;z&TzUII+f$<$F&a|ze{yryX%-b;GhF41s!9B-+tJa2G=g8*(ORV5^L|#`Qkzjn1+NSmicfCD"
    "+i$7wT-l*WmBfilY07`}7yZ7`KYSyUN<&*L6E4fD(U|;tS*tEBb#e<E?@M%`!RaISpl9WM#(XaYQaO)~Om#Gjg@cjsZi6$5B^y=F"
    "u6%jr&L2}(9i{HA#MWF%QN`6DjK{eAQHp>tP!y2h508}WY?mCpZAZ-PCIc(^*^apGi@MGRYFbCQ*y_5`bK>3)B$b0LNeyl9$2brV"
    "qeY9Bg5IHQLZRYocMOBIB9N-WrN{k4DIit&ht&LAbO{z-6!_HT4lB~tWb_<X!pg3PBL&_a;DwI32R#+3C;8Jy(}PA$oEw)!r$`-?"
    "F1^sF$X-3h?@Uh1rN>yE1%I8yM2n;t!-o2eqBHNVt`TDp<Y*q0Ie*JsLnG+PzYKbK)K$M~uV=y!W3-ZYA#f++JWv7Nqz-ol&Kox<"
    "lAk-f?}P$R^j)4%B}J^sHu^0VecDmGyW2!y5ug9sbRY0kJu!%K8*GH&VJ?89=A-(#1T2gSnD~sTK-?GiyTw+l5BZZ5se}M#->8O%"
    "Rm6JE!GtvQKNNtneAab#T;9eH*W_A?+k@-u!n;%UT8%|;D$Qe4ITI#30U4d{b@|z<*OdRGp`ITBKePG&W<$Alg?7DL{p^+H01td9"
    "uel*@RW=D2G83wy;=PA#1!Q^}Lrt+BA_epi4V8a<+Y-Ha*(p*rvIeP!hq<LtnN|P}@y_AUsv2r=^C}S8{YC!rAsdR7+C|)LB~v9D"
    "N~)!Cf&L6S(4bX-l>b1<f272G?|L3nJ*&B0Xj>}wk|%i`Q{xSyp;mGI#qfKme{?97XEm#R?#iKvEb_>I4i#38UCgX<a!U60qoGp3"
    ")=fa5<mGK0=|=7vJ@LD*#>=`ZrhQ2_Jjt)duZ#dWNqw#0It>MgF_g4I{7XP{02o&4q9T)WN3J4r+8GpKdxt1rwZPm{=O`WRTx(Z`"
    "`0+>X(DKh2<*+61SN3qESEk`tYrHZIN80qiekgSuv0hrd@`4l-Qmx6A0W82NM65boU<G>rbji_Bp4jCr@(6t3fOhZT4cwl!0~(;Q"
    "gpps0TCO551VQ@5PUh|Pu6Bpn8`gGLIDJF3I^qKW?Uk_8yB!;QvBum?@}A!xmq&6#{NjgPYv2lr33ZyR6{s{t3k!s%K|f2<#>1*X"
    ")FrGK6nw(UL3yKNoX5hy2mPNP6w%}mcLX=d`IkgX(b3}T?RPXx@<}b&Zws#{b<0(14ximH5}-b=N=?<ez$7zMkioN{{}yl`0nt18"
    "W!h&J_eT5Nb8iZRGZ_&a;2Cg$3FrXB?3uRBR4s4W{#NBDo|tL9kA8;a*Zs|BsgqxKasMV$lX(N8=c$^ST=?C&a9A~`hLwC!+E;68"
    "WR1KPhKa`Wr<TdnWTX5r<II(+sX3$9TdutReE!r1DU1Kgv>of#lczSa25-rBW%Tr^<<7pXJvm5)J3ajuy52V0JiMncC>R2IQ#*?8"
    "4r^mWmUd5jYPe%Ik!jS(rdHU-t|DTW^(x5i(A3PK)ZK&Pm}gIol(JKv>$A015Nj0M)6*CFkhmYhwkI!?@`~Mx>+kH7ZQ$Ie6gfEU"
    "wFZS9o;VwsBHL7|6J&bfQCbCS<huf7|4rqT08k-Da3lOTU=-&nPg!jgH4LDRvHR^v{`QoA(NkUkN<aaE<x&)O5k`J%>=^x>H-kmw"
    "aHCqJC&Kz#;jyn%=_rvsaQ^i%B693}9Gh=tf;pVT{k{$6v`_B%Tn66)K%dybg$oyXyT+nwUo4G1g&G&*%|>N<M_WryZ93S_EqbWc"
    "=|n3dV2=~!%yqsQ7<NdZ4)vL%7bN1fs1F4omoo{QiGo}dd)K*U2O57QY87bTt$<vRlxF2*RPTCa5Gw14GCDdnLm)cBs!05UXxWI3"
    "-A)&wR3K#fohXiKmi@qY|0cnwa->cTM(hj0co~-t-Ng*fIln+DDxB9+8jber?+by;3NNoCg1Z8H-THO*#ZqkhUN{BsfcA*DbP)n<"
    "Qe%rr-Qu+9R5+!XN)npCf8gKY2g;2Mm_`=oBNh0_RiZ&`c^p&xH_zuNnN?s!RW*T?E2gSZ_eWX9e{;u18~H66zH?<M5mNX-(qG%S"
    "jtA#vq5JK~gqKadSf&$7ZL9*YAsN5a)kRarTdrMN5uC)Y`_@wq#T2_A@_F_(En@7$HFHN=hk{5=zci~{OHr8=*&YeffrbhRLZFC;"
    "WLf!84wW!Oge>*eyo1JO#Tus$`5KW}s3;NPv1Uo-PzdE9r9n@&_f||k6#F}6{5Kj(?Z5oP+2@}nvcc9|X*QLKxj2R#I6{+_J7zMs"
    "!!>pEJ=@Ftith#N#}_*wCmK<j6(w<)h2H@AB36!M+SKSZzu>O`$r%7#o}UzaDyhfxvf*P#SY1ynD`x>}*o;FI-*M`>0~S`+<n-GM"
    "BeBC011w6R3o`_o-8~iTk-UpPYwO%&e2)k`Nd+S!o9C=Q?A9({9R&oFT(71=dERqeylWr_2-F|i-+T@O>dX~|aJC0+6ua*jl*Dub"
    "TF_LYY&HrNa++DyH1Gl#2=Cp0>PiTMqLd6k?Su3u5w(tlWfV;>gkBJjSHuBi3B$&BFqPmVHtyI5TnsI@H46_5(Er#H5xneGR2!4p"
    "W41Zo+{MI7H6wHwdJ+$ag1ma8LB8nyF7^jA!Fbesb&1R>UerNfKrlP>PpF%(AZ7;Y-O_gBiQ{}Kq2ed?)aE6-voUA<*>1v!N~2%{"
    "t#M3_PZQOy(Hf=f9nolwdfI^kTcc#qo8PTbzgwgJC9P3Ud-h;!l(O?rqcuw1Kd5Sr`p;{clx<if!u8i*0xZ+!H(KyFTJSeo@Lzxy"
    "{7-5k`?U$F(Cb3K4gNu*4yt||9e5w=x7mX5#3|S?r%vX;>p6avu4^l4yG#`&0wx{s3)$CLxQeGVJkbG#{^zDUFkyeKS#EDqasyJv"
    "qwtMeL#t_>>db813R?v`vU(JC6FOx8WG!afcJNfeT5K>N&s3Dxk-*ZZB$J+s9Xi7=dHP`bq^7w#1oUfiG&A|ot;C5vJ(@)>->;QX"
    "pVoDsR&$@#aR0@()IjDh*JFJ^KTkZWk@LrM;KE_N0}I(LEMy8>$gWQ|WHEOJp3W)vw%ASzlQIZgqukj!3#l=;K+w!dw6)qvfHKUR"
    "0H@p<T1juUa?cFb^$Pr2axbXer?0jgJoOWomA}S)Ei14#rtMd$zDqj!uK`MCng<o*59(uTF%>MNSc~juFcHRYc0U=D?bRpTUhU;~"
    "RnB2a;Y`Wd4NE4Q^`U_F0fH@ZTVYx*T3_%v0!bEScdD^5+ycMWJH`0rC4s+Mj@)}d%W}w3vrJ|9pluk{WBc{fn+aDAiGH4O8E+~<"
    "5!hZVU8toDzugw#AGwZmf6FZUn8XlJ`C7tQp>%QDE4xpL`d&&sq%s|ro6rUg$^!9@3GY+!U%M3=XOp*Sy4mV)Edz{E{3InPeJKCQ"
    "hCC(VYYI-EtCPQZChKZPwx;=@db)P|_Tss?_=rnObq|&*0H~1MI^`LJ|G-<AwthMF_TTUiBD;ZtllavA^*{WZ{qq0uKZN!EAVtj-"
    "j}`=;7ab>X#XVZgPH%U90%^E$e*i6%<Pq@G@|cILm~dmG^kJGZBDJ|?+>*B7JHd4F3%mlw3zi7-f49EG8Yq<>8rO?XsO_>(FTCjm"
    "o8TaoEciYJN}DW54iKuEICu4mSt!Tj)3{Rrf3k~~+4Q5K_?>F>#<8LJCnqT(@Iz@woz7+A_fS6_YLnC*3bfroMn0r$B@N|OWqw=|"
    "jjS|OsyTtDQuoM3QL+>@8j74tYhCQP87)ZVP>4Ly>q`Kp7ILRpSA66yv3po5_uACHw0)+H%Ap8%{475!gFr}cB_E1#u_ZeuuhM;M"
    "on0FI93`NXB}ALKG_{n8b)YcCMeJ7LanrtOP44&`ghPQ{cLYa|hgbgKIl92ML!H<%tBmABnEPLI3BfD73ZA+HZxVKH>kadi=mHQL"
    "CFMnEJR*vZH>>7noZ=HPC>lNDrg1>*C5Rg7poX6-{w*OI_{!Co!jjKCSD?^KzYoAmE{#YUyTt3RN8n>LJig3)>ac&kmShsLsdiAX"
    "H6$6G2zimkOoo)RPlP2BB|d>KR|s&<%)6{1+`FHOUJm$!v*Z;oM%YtH#eg3kh`JIH&scU4>}aWZs6n{C>9OIMIF_^zksZAx5~t=x"
    "!-YRekJ#!=4%^>Uj@z?}7{D?Dy+MHH=Hu8jYLfQ1noJG8^Dfn@YcjjLtZSS2&ehr|LN-eDt+`*WBW>iK9oLewo>e>C_U45p%3PK@"
    "(y-#LxgIC^hCJVQ0!Nll*gP(HW+`QJ*j$J26!Gzdp#HMI4RUT2QaUc{eM4A6RExKVKllbIR3zCY&rOeiLuQ8qQlwcE?vb4_BF)v-"
    "76`1fAAH`2QPr(6@J39?WBMxN$n?67@dL!A>Yv!P;BiZchLk`SojM!3VnYo<9J1EA3rk6n@rHPhZ32G7nT(_`51-q#8EC3Ol`BWk"
    "#h9csPQx4{=k@!rZ-4=A7^zKqkflUE2L^7aeS7q=(8{4)5BEsL=`hW=K)%ug%N@I2I?*}1-|$c$0pxwF_<MET_}HRUXEx_OIaEoV"
    "ty#$Or@ey~_aG)K?nc5fG!Kn!A->owThtSA+0PnFZU)v*BsCjcq*{?%>fV%TY*BR)47VI}_GCF75k8|u=vi`>3O9bbvL){mZS-cx"
    "ovyQwK0#br!2ykqM<oA9<Obx7irlw!a{7VsmgQ^#GvX4GKDd}XO#D)NEFgfdR{jBQ##Y#jDHo`YV{#ieF{3GixJXAVkm}<FNu(H!"
    "O=xZRgztWzi9&-=+eGqjnW(0P5VWA#n^;>VoPsLXHb85BBi4%y6=^x{bz6*p_+DF>+1cHEVj{7;%e3wfxW~RoI^|aB8y@Kdf1-PN"
    "qomSSoQ;N<aw~hvxs;(8u?%8lFS8=ibg9G{Ejgr7$y);-lJ>YXnPve-)*rzwve13eS&H&7q6y@`@fy~W5C(~azwRKZ^v0dVe))4G"
    "5v|YJ>!FVGTb8NIi^w(9TAQHk(~o}YIJL`|>B-SMLb7ukBcVQwoGk|Z-c#J3S1$laPtRMc%3V99n?H-`FXm0N$0}VmnuN?wHZ#=F"
    "Ghg9}g?Ol@;>81fG_%O)Z6(90VspsxORH{Me8Dnk=dEnQY4+U=J@Av+t^?(l?VbpA!4f3Kq=QdcMC}bn8gdkYi@Vr^5DPd9M6(TU"
    "2{Rq<soOOx(KP1~Qj2eV!%?;$&5Wwzwrpd`B+l=1Csmz6oy!_8eaiwv{-5y~?2og;<ppX@!tO)qD2Q*Rf~aQv*IWXg<X%=n#$DdE"
    "vF7GEdP<r-5uk}qIyl+zD4enI%vQ)1qtc-Srh<dmq$Ef!D8GGR%h*R{Vktp86#CmhM0I+?v(bp}jp}?DgxGm$!&7puVMmCk<K}`>"
    "sOzWOav_F>=!vGUAbU`YsMa!-7oXqqv4iA<&i8M#Jew&=^-Q_7=k?aC{q|Ds@{*E2z+`#W2#wRk={VB64a_f&r~aL?mqp&QRw-RP"
    "3r)jp4?o~a=NvpkMbiSrOT&fKM3U03W6%4^R|<9Rx$qXUX&pr<f)q%uZ#3C&>6OgkTj;bbQ(YxhBhm@fEqU=FXtJ4at#vP{7TuM`"
    "^B&UA3U$?(DK))Lnsfd^_yUFRcP;7f8Rxh1;WgmlT%Ko|mlW3VFKRPiXKwj=G^TwC@<T>iBHI)u54Mbli&|>R-qNx;AiCFJT~o^z"
    "*qw`1kf8a>8bAji#!`(k2&OKqDud8AT_(1saY4^;x$ne0CI#6=?v`y#v;}mI!9090avM60Wvf&CE0vVcJ5Do<CxDv@xANImZli`w"
    "`7)J46E=snBtyq1^VS!|m8+Ee85tz{v3qV>_u=vlRCU|c6W^u2&E-o%TZ|Toi*HM$s$SJP!c5DxX`jmlZcx#K87p69@OvyYK_o{*"
    "xlJJ@=oM?=smA!@5|*^Q&Xs7|YIzB_G>C$dmRS&*kkznw3Ybxp?n$-GH|%bJ)Mj7*$~B`p%V!gOA_+!i^#3|y!D78a+C`u;1Ee5G"
    "MHM)3K1K~IcegfvkKEkny!4LA4_Q@+!CpS5tPKJB($}cBgIN2`?_Dx2UlL`tRQMji?I)yJW?xIagoerkm*OP=2bJe2kO+WZrFIHp"
    "Mrb&>AK3n<f9=?S{x+a?k?TBD;z6<fG%LSW7|vln)N0P2WE+L_iABJ*>!Iwjav$RGfq{TkI*`+i(l)vlJmBQ_rl4y2=1W}L&!blB"
    "I5_KMCxhZ^le9eHl4}<Cvj8dLomyGNBvDV4Y?A!PmR8pLvFJ>sVpTm71PRo5lIXpuU%=mImFO?!XFCAfI8YfH`x@GBDgtflZJQCd"
    ">4s8hX#&_wUvqZ@E?8Zo0Bp(SIE*=%?jyJBa$f`1=LT6c+<*H1^!({^{rLwBR$YS+P@t#7zyIey{6E3ty+h;ff^?$5xbr~L?*8WW"
    "oeS18?rh0hoDR#@SWH^b9yw6LD~q3J%|&R^i3kmSsoM=-h2E$^NJ_;YA95l$O3Wl}E=q?^)cI!Bn>93nNdu5vka?^gR@grI<5%RT"
    "`%0oa{e^vsZe(64Hn0SMXm@oDFX&#tA4J@47i3<D{9e|I56S>4JpdsiBvE@UUEEoVEBLV8w%|%;4AG2C_M3E~yc&l87d)W?);qrN"
    "4{71AbpF0oN4f+qew0b>Y3FntXGIW7R`6BQ-G(d;;;i~~Fh`_x4_fJ$BgtBc@m73CIUn)M@93Yk7*wlH#IbJA!5=U0;=T%Zg;KUs"
    "XCJv}W>w0m0JDk>yS_`faHsqa1uTUCJ>=547dy9SkBKs<d5G$7Aflmx2HYRS4?cVri1Z(N4s!f%TV-vXn<7KHN+qK`%8=^yP@-tt"
    "Ywe}r%S-#WcSAnbv$pQ?!s=z&-k7TH)aYd4)yEU9Gu3!5J(je4to!Ge_$g|2<;>EDH9qvms&)5tu0l}0wFY0ej3<mXtgjp%#2;vC"
    "ji}F<s*ElXMVOd+H-wtwcKs3^2zw?SrCvTpUL^Iv1<_83Jm=kYx2h%PSU8>=AMHuEvgqfgy<h^nxzp`3DOtTy@CZ7-AIhhJMS+E@"
    "05^{}oDQnIt8#wDrX&QON%|;YP@<LHn^^3b^~Eih5-L)8OH^2*KwVzAIby=c0It+gyg4ewGZ(EV12Sn4%r}e&azoYDHTQ*$==;v9"
    "^S)3rl#in{vci~xH=|j=6bnUBqE~p7>bj@Zuil)}Q;VmeJIrh2YFz?}9t*LW=3lQ@W5xCN{^kF)n*&vEuj5$IxjB-r*S`6LI(-H8"
    "Zw?Z+u#BXC^Uk~NiQ!qaZBKQ(3%c)Is9}jFqDM+Poi1RhIsZ>#so^0EQV|ASg9Bo7-!13q8J<|B>y8_0TQod90Qip4r<eR4CWH#O"
    "|DB`bMur2gE-B2~FE8QFvY$-oyc}=-_r9`UpU^-4A)SBGEBlwOA;~0oL72_C3&44!|KtsVv$E)xE&V#mof<2{v6#7BL?p~M>us>1"
    "H9WzOxi3)}#OJaL1}k;=>=8`0G!K|PyAix6#XT`7@Jay#MEbZ8{|_xahFdH&3}~3U&R=k`O`3}fP!PG`TwH|iT%OtA&VR}`q=(`Y"
    "7X|OllgO2HMoVJcSO9RIH$E%I0vKG0?|dect7?+lwe<nFdYT{^#5zFxa|fb_J=u+qR}KN<rT_+0h9DH6@cRk6@wjkqc9_Cr5mW*A"
    "!0x;M*u-zS;?l&q{HGaTtmmf#%b)47u`fBo-0W#Mdy1bsHhox-hR&m}eU<pB-B|qU+_sux?=KO-dW0b9!NvkoWsM-}s)x)FxpAUH"
    "cn8)uA+<$yASeYSEX}Y28)qXR=gM*+`0ywMaFjp%A@}1c&L@VM84uVRqz5pw!RfQcakAMV`)0Arm|*ru5PNNEnMp28Y<O|)i(2l3"
    "h*cdj=YCZ)c|KA#dB+FQ1l3_iLC*pjHWi3fH_BH?|E&P9Uq|_WbAc`pxz-T#>1MumvPHMO)rsh+AnRe}sa+Cr3jZAx0sJNAh#&zg"
    "OSTNNoiS&{Gw+bKvrYCKKl?Bqa$uzQs>1EUv$h(|!H2zLFg%n=1X#%`%@?v6XB$8SNfu4y7d`cM@=>xwI3;l{-1kXu=5jiwOhN8l"
    "Z5OCdhY~48*l;%IJsJr~${Nrt*p*ov&x01BK<@h;ABv1i62eO?T=zYSvm6=<(A+>!3FJo;zZ}Abq9{sIx{Avvi!Cv~I20*$-Li@T"
    "jl1LSjfG-jCS?$YO87=Hgp=nxEe?g2mOA$gua&xj)dox|?UMQqbDI|NH_qg@TSqZ^we`zNh-s<cp4P90V;nIOpP3rhiu&2;lkQNU"
    "4Y;8o*3v=ZDnbPrz!>!m%R%Qdm_tqb8N`~kkkZpxhMEBxU|G|(LpM^SCRuLxT7}vyZ5w+;U^5+1rn5-XjxQUzMFEZ|k93owd=lX5"
    "-bFmGGa&Y1^L?Sxqqf`{H$ZwKl%_&`0&bkEn;eLBC%!$Jq!2)%F4ke$1DlJTfq5obAOI?>W04I;qTgx6haZvAw$@p7jl_Em2QpCC"
    "_r6MxsDD(U6zF^bXLQJy>^*JtN5kf`J4ai_k-ZOmij#vPDJc=>0pT5YaQu75E`R*L`~Cj^0kE6u(f"
)


def _load_glyphs():
    raw = zlib.decompress(base64.b85decode(GLYPH_BLOB.encode("ascii")))
    data = json.loads(raw.decode("utf-8"))
    styles = {}
    for key, st in data.items():
        glyphs = {}
        for ch, g in st["g"].items():
            glyphs[ch] = (g[0], g[1], g[2], g[3], g[4],
                          base64.b85decode(g[5].encode("ascii")) if g[5] else b"")
        styles[key] = (st["asc"], glyphs)
    return styles


STYLES = _load_glyphs()
FB = bytearray(bytes(PAPER) * (W * H))


def px(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        FB[i] = color[0]
        FB[i + 1] = color[1]
        FB[i + 2] = color[2]


def blend(x, y, color, a):
    if 0 <= x < W and 0 <= y < H and a:
        i = (y * W + x) * 3
        if a >= 255:
            FB[i] = color[0]
            FB[i + 1] = color[1]
            FB[i + 2] = color[2]
        else:
            ia = 255 - a
            FB[i] = (FB[i] * ia + color[0] * a) // 255
            FB[i + 1] = (FB[i + 1] * ia + color[1] * a) // 255
            FB[i + 2] = (FB[i + 2] * ia + color[2] * a) // 255


def rect(x, y, w, h, color):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(color) * (x1 - x0)
    for yy in range(y0, y1):
        i = (yy * W + x0) * 3
        FB[i:i + len(row)] = row


def frame(x, y, w, h, color, lw=1):
    rect(x, y, w, lw, color)
    rect(x, y + h - lw, w, lw, color)
    rect(x, y, lw, h, color)
    rect(x + w - lw, y, lw, h, color)


def line(x0, y0, x1, y1, color, w=1):
    dx = x1 - x0
    dy = y1 - y0
    steps = max(abs(dx), abs(dy)) * 2 + 1
    r = w // 2
    for i in range(steps + 1):
        t = i / steps
        cx = int(round(x0 + dx * t))
        cy = int(round(y0 + dy * t))
        rect(cx - r, cy - r, w, w, color)


def polyline(points, color, w=1):
    for i in range(len(points) - 1):
        line(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1],
             color, w)


def circle(cx, cy, r, color):
    for yy in range(cy - r, cy + r + 1):
        dy = yy - cy
        rem = r * r - dy * dy
        if rem < 0:
            continue
        half = int(rem ** 0.5)
        rect(cx - half, yy, half * 2 + 1, 1, color)


def ring(cx, cy, r, color, lw=1):
    import math
    steps = max(24, r * 6)
    for i in range(steps + 1):
        a = 2 * math.pi * i / steps
        x = int(round(cx + r * math.cos(a)))
        y = int(round(cy + r * math.sin(a)))
        rect(x - lw // 2, y - lw // 2, lw, lw, color)


def fill_poly(points, color):
    ys = [p[1] for p in points]
    y_lo = max(0, min(ys))
    y_hi = min(H - 1, max(ys))
    n = len(points)
    for yy in range(y_lo, y_hi + 1):
        xs = []
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if y0 == y1:
                continue
            if (yy >= min(y0, y1)) and (yy < max(y0, y1)):
                xs.append(x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            rect(int(xs[i]), yy, max(1, int(xs[i + 1]) - int(xs[i]) + 1), 1,
                 color)


# ---------------------------------------------------------------- text ----

def textw(style, s):
    glyphs = STYLES[style][1]
    total = 0
    for ch in s:
        g = glyphs.get(ch) or glyphs["?"]
        total += g[0]
    return total


def draw_text(x, ytop, style, s, color):
    asc, glyphs = STYLES[style]
    cx = x
    for ch in s:
        g = glyphs.get(ch) or glyphs["?"]
        adv, dx, dy, w, h, data = g
        if w and h:
            base = ytop + dy
            for row in range(h):
                yy = base + row
                if yy < 0 or yy >= H:
                    continue
                off = row * w
                for col in range(w):
                    a = data[off + col]
                    if a:
                        blend(cx + dx + col, yy, color, a)
        cx += adv
    return cx


def draw_text_c(x_center, ytop, style, s, color):
    return draw_text(x_center - textw(style, s) // 2, ytop, style, s, color)


def _tokens(runs):
    toks = []
    for style, text in runs:
        words = text.split(" ")
        for i, wd in enumerate(words):
            if wd:
                toks.append((style, wd))
            if i < len(words) - 1:
                toks.append((style, " "))
    return toks


def wrap_runs(runs, maxw):
    toks = _tokens(runs)
    lines = []
    cur = []
    curw = 0
    for style, wd in toks:
        ww = textw(style, wd)
        if wd == " ":
            if cur and curw + ww <= maxw:
                cur.append((style, wd))
                curw += ww
            continue
        if cur and curw + ww > maxw:
            while cur and cur[-1][1] == " ":
                curw -= textw(cur[-1][0], " ")
                cur.pop()
            lines.append(cur)
            cur = [(style, wd)]
            curw = ww
        else:
            cur.append((style, wd))
            curw += ww
    if cur:
        lines.append(cur)
    return lines


def draw_rich(x, ytop, runs, maxw, line_h, color=INK, max_lines=None):
    """runs: list of (style, text, color). Wraps and draws; returns end y."""
    lines = wrap_runs([(s, t) for s, t, _c in runs], maxw)
    cmap = {}
    for s, t, c in runs:
        cmap.setdefault(s, c)
    if max_lines:
        lines = lines[:max_lines]
    y = ytop
    for ln in lines:
        cx = x
        for style, wd in ln:
            cx = draw_text(cx, y, style, wd, cmap.get(style, color))
        y += line_h
    return y


def wrap_count(runs, maxw):
    return len(wrap_runs(runs, maxw))


# ---------------------------------------------------------- illustrations ----

def ill_kyiv(x, y, w, h):
    rect(x, y, w, h, NAVY)
    # missile streaks
    for sx, sy, ex, ey in ((30, 6, 84, 40), (150, 2, 190, 34), (258, 8, 226, 38)):
        line(x + sx, y + sy, x + ex, y + ey, (243, 156, 18), 2)
        circle(x + ex, y + ey, 2, (255, 220, 130))
    # river
    fill_poly([(x, y + h - 22), (x + w, y + h - 30), (x + w, y + h),
               (x, y + h)], (52, 92, 138))
    # three bridges with bursts
    for frac in (0.20, 0.50, 0.80):
        bx = x + int(w * frac)
        by = y + h - 26
        line(bx - 36, by + 4, bx + 36, by - 4, (216, 222, 230), 2)
        line(bx - 30, by + 3, bx, by - 14, (160, 170, 182), 1)
        line(bx + 30, by - 3, bx, by - 14, (160, 170, 182), 1)
        line(bx, by - 14, bx, by + 6, (160, 170, 182), 1)
        for ang in range(8):
            import math
            a = 2 * math.pi * ang / 8
            ex = bx + int(11 * math.cos(a))
            ey = by - 8 + int(11 * math.sin(a))
            line(bx, by - 8, ex, ey, (243, 156, 18), 2)
        circle(bx, by - 8, 3, (255, 214, 90))


def ill_cyclone(x, y, w, h):
    import math
    rect(x, y, w, h, (223, 242, 239))
    fill_poly([(x, y + h), (x, y + h - 16), (x + 90, y + h - 8),
               (x + 120, y + h)], (178, 205, 170))
    cx = x + int(w * 0.34)
    cy = y + h // 2
    pts = []
    for i in range(160):
        t = i * 0.11
        r = 2.5 + t * 2.05
        pts.append((int(cx + r * math.cos(t)), int(cy + r * math.sin(t) * 0.8)))
    polyline(pts, TEAL, 3)
    circle(cx, cy, 4, TEAL)
    for i in range(9):
        rx = x + int(w * 0.62) + (i % 3) * 34
        ry = y + 10 + (i // 3) * 24
        line(rx, ry, rx - 7, ry + 10, (90, 140, 160), 2)


def ill_markets(x, y, w, h):
    rect(x, y, w, h, (24, 22, 20))
    for gx in range(1, 6):
        line(x + gx * w // 6, y + 4, x + gx * w // 6, y + h - 4, (52, 48, 44), 1)
    for gy in range(1, 3):
        line(x + 4, y + gy * h // 3, x + w - 4, y + gy * h // 3, (52, 48, 44), 1)
    pts = [(x + 14, y + 14), (x + 68, y + 22), (x + 118, y + 17),
           (x + 172, y + 34), (x + 228, y + 46), (x + 290, y + 60)]
    polyline(pts, (231, 76, 60), 3)
    for px_, py_ in pts:
        circle(px_, py_, 3, (231, 76, 60))
        circle(px_, py_, 1, WHITE)
    draw_text(x + w - 64, y + 6, "sansb13", "-6.2%", (231, 76, 60))
    draw_text(x + 12, y + h - 24, "sansb10", "TAIPEI", (150, 144, 134))


# --------------------------------------------------------------- the map ----

_LAND = [
    # North America
    [(-165, 68), (-150, 70), (-135, 69), (-120, 71), (-105, 68), (-92, 66),
     (-82, 62), (-79, 57), (-88, 55), (-94, 58), (-97, 53), (-93, 48),
     (-88, 47), (-84, 43), (-79, 42), (-75, 40), (-74, 44), (-68, 44),
     (-65, 44), (-60, 46), (-64, 49), (-70, 42), (-74, 39), (-76, 35),
     (-80, 32), (-81, 26), (-84, 30), (-89, 29), (-94, 29), (-97, 26),
     (-97, 22), (-94, 18), (-90, 15), (-86, 13), (-83, 9), (-79, 9),
     (-82, 12), (-87, 15), (-92, 15), (-97, 17), (-102, 19), (-105, 23),
     (-108, 26), (-112, 29), (-117, 33), (-122, 37), (-124, 42),
     (-124, 47), (-130, 54), (-140, 60), (-155, 60), (-165, 60)],
    # Greenland
    [(-45, 60), (-40, 64), (-32, 68), (-22, 70), (-20, 74), (-25, 78),
     (-35, 80), (-50, 79), (-58, 76), (-55, 70), (-52, 64), (-48, 60)],
    # South America
    [(-79, 9), (-72, 12), (-64, 11), (-55, 6), (-50, 0), (-44, -3),
     (-35, -8), (-39, -13), (-40, -20), (-46, -24), (-52, -28), (-57, -34),
     (-62, -39), (-65, -42), (-67, -47), (-68, -52), (-70, -54), (-73, -50),
     (-73, -44), (-72, -38), (-71, -30), (-70, -22), (-70, -18), (-75, -15),
     (-79, -8), (-81, -4), (-80, 1), (-77, 4), (-78, 7)],
    # Africa
    [(-17, 15), (-16, 21), (-13, 27), (-9, 31), (-5, 35), (0, 36),
     (10, 37), (11, 34), (20, 32), (30, 31), (34, 28), (35, 24), (37, 20),
     (39, 15), (43, 12), (48, 11), (51, 12), (46, 5), (42, -2), (40, -8),
     (39, -14), (37, -20), (35, -26), (32, -29), (27, -33), (20, -35),
     (17, -32), (15, -27), (13, -20), (12, -15), (13, -10), (9, -5),
     (9, 0), (6, 4), (-2, 5), (-8, 5), (-13, 8), (-17, 12)],
    # Madagascar
    [(44, -16), (47, -14), (50, -18), (48, -22), (45, -25), (44, -22),
     (43, -18)],
    # Eurasia
    [(-9, 43), (-9, 48), (-2, 50), (-5, 53), (0, 52), (3, 54), (7, 55),
     (8, 57), (10, 58), (12, 56), (18, 56), (20, 54), (24, 58), (21, 60),
     (25, 62), (24, 66), (29, 70), (40, 68), (55, 68), (70, 70), (85, 72),
     (100, 72), (115, 71), (130, 71), (145, 72), (160, 70), (175, 68),
     (178, 66), (170, 60), (160, 56), (158, 52), (150, 50), (142, 48),
     (140, 42), (135, 35), (130, 33), (126, 35), (122, 32), (120, 28),
     (115, 24), (108, 20), (105, 15), (103, 8), (100, 8), (98, 12),
     (95, 16), (92, 18), (89, 22), (86, 20), (80, 15), (77, 8), (73, 18),
     (68, 23), (62, 25), (57, 26), (52, 27), (50, 29), (48, 30), (44, 29),
     (42, 32), (40, 31), (36, 36), (33, 36), (30, 36), (27, 37), (23, 36),
     (19, 40), (15, 38), (12, 38), (10, 37), (10, 44), (7, 44), (3, 42),
     (0, 39), (-2, 37), (-6, 36), (-9, 38)],
    # Britain
    [(-5, 50), (-3, 53), (-5, 55), (-8, 55), (-8, 58), (-5, 58), (-3, 57),
     (-2, 54), (-1, 51)],
    # Japan
    [(130, 31), (133, 34), (137, 35), (140, 36), (141, 40), (142, 44),
     (140, 42), (138, 38), (135, 34), (132, 33)],
    # Sumatra / Borneo / Java / Sulawesi / New Guinea / Philippines
    [(95, 5), (100, 0), (104, -3), (106, -6), (103, -4), (99, 1), (96, 4)],
    [(109, 1), (113, 4), (117, 6), (119, 2), (117, -2), (113, -3), (110, -1)],
    [(106, -6), (110, -7), (114, -8), (114, -9), (108, -8), (106, -7)],
    [(119, 0), (121, 1), (120, -2), (119, -3)],
    [(131, -1), (136, -2), (141, -3), (146, -6), (150, -9), (147, -8),
     (142, -6), (136, -4), (132, -3)],
    [(120, 18), (122, 16), (121, 13), (123, 10), (122, 8), (120, 11),
     (119, 14)],
    # Sri Lanka
    [(80, 9), (82, 8), (81, 6), (80, 7)],
    # Australia
    [(114, -22), (113, -26), (115, -32), (118, -35), (124, -33), (129, -32),
     (132, -32), (135, -35), (138, -35), (140, -38), (145, -38), (150, -37),
     (153, -30), (153, -25), (151, -20), (146, -19), (142, -15), (142, -11),
     (140, -13), (136, -12), (135, -15), (132, -11), (130, -13), (126, -14),
     (122, -17), (118, -20)],
    # New Zealand
    [(173, -35), (176, -37), (178, -38), (176, -40), (174, -41), (173, -39)],
    [(167, -46), (170, -45), (173, -43), (172, -41), (169, -44), (167, -45)],
]

_PINS = [
    (1, 30.5, 50.4, 13, -13),     # Kyiv
    (2, 84.9, 19.3, 11, 9),       # Gopalpur
    (3, 121.5, 25.0, 11, 11),     # Taipei
    (4, 19.9, 52.1, -15, -13),    # Poland
    (5, 4.35, 50.85, -17, 9),     # Brussels
    (6, 30.7, 36.9, 4, 22),       # Antalya
    (7, 12.5, 41.9, -15, 11),     # Rome
    (8, 127.0, 37.5, 12, -12),    # Seoul
    (9, 44.4, 33.3, 20, 18),      # Baghdad
    (10, 35.9, 3.1, -7, 14),      # Turkana
    (11, 56.3, 26.5, 20, -16),    # Hormuz
    (12, -77.0, 38.9, -5, -15),   # Washington
    (13, 172.6, -43.5, -7, -15),  # New Zealand
]


def _in_poly(lon, lat, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > lat) != (yj > lat):
            xint = xi + (lat - yi) * (xj - xi) / (yj - yi)
            if lon < xint:
                inside = not inside
        j = i
    return inside


def draw_map(x, y, w, h):
    rect(x, y, w, h, OCEAN)
    frame(x, y, w, h, (170, 178, 182), 1)
    cols = 100
    rows = 46
    for r in range(rows):
        lat = 84 - (r + 0.5) * (140.0 / rows)
        for c in range(cols):
            lon = -180 + (c + 0.5) * (360.0 / cols)
            land = False
            for poly in _LAND:
                if _in_poly(lon, lat, poly):
                    land = True
                    break
            if land:
                dx = x + int((c + 0.5) * w / cols)
                dy = y + int((r + 0.5) * h / rows)
                rect(dx - 1, dy - 1, 2, 2, LAND)
    for num, lon, lat, bdx, bdy in _PINS:
        px_ = x + int((lon + 180) / 360.0 * w)
        py_ = y + int((84 - lat) / 140.0 * h)
        bx = px_ + bdx
        by = py_ + bdy
        line(px_, py_, bx, by, DARKRED, 1)
        circle(px_, py_, 2, DARKRED)
        circle(bx, by, 9, RED)
        ring(bx, by, 9, WHITE, 1)
        label = str(num)
        draw_text(bx - textw("sansb10", label) // 2, by - 7, "sansb10",
                  label, WHITE)


# ----------------------------------------------------------------- page ----

MX = 26            # left margin
IW = W - 2 * MX    # inner width (972)


def section_head(x, ytop, text):
    rect(x, ytop + 1, 12, 12, RED)
    draw_text(x + 20, ytop, "sansb13", text, INK)


def build_page():
    # top strip
    rect(0, 0, W, 28, INK)
    draw_text_c(W // 2, 6, "sansb15", "39 STORIES • 7 REGIONS • 12 FIELDS",
                WHITE)
    # masthead
    rect(MX, 32, IW, 3, INK)
    draw_text_c(W // 2, 38, "serifb34", "THE WORLD TODAY", INK)
    rect(MX, 78, IW, 1, INK)
    rect(MX, 81, IW, 2, INK)
    # giant date
    draw_text_c(W // 2, 88, "serifb44", "Friday 20 November 2026", INK)
    rect(MX, 142, IW, 3, RED)
    draw_text_c(W // 2, 149, "serif14",
                "Every story happened — or was first reported — on this day.",
                GRAY)
    # key numbers strip
    stats = [("110+", "MISSILES ON KYIV"), ("±400", "DRONES LAUNCHED"),
             ("300,000+", "PEOPLE EVACUATED"), ("−6.2%", "TAIPEI'S FALL"),
             ("100,000", "YOUTH VISAS A YEAR"), ("51–48", "U.S. SENATE VOTE")]
    sy = 170
    bw = 157
    for i, (val, lab) in enumerate(stats):
        bx = MX + i * (bw + 6)
        rect(bx, sy, bw, 46, LIGHT)
        rect(bx, sy, bw, 3, RED)
        draw_text_c(bx + bw // 2, sy + 6, "sansb23", val, INK)
        draw_text_c(bx + bw // 2, sy + 33, "sansb10", lab, GRAY)
    # region bar
    regions = [("EUROPE", 11, (36, 86, 166)), ("ASIA", 9, (176, 44, 36)),
               ("MIDDLE EAST", 4, (214, 116, 34)), ("AFRICA", 3, (34, 139, 80)),
               ("AMERICAS", 5, (125, 60, 152)), ("OCEANIA", 3, (17, 140, 130)),
               ("GLOBAL", 4, (110, 118, 125))]
    by = 224
    bx = MX
    for name, count, color in regions:
        segw = int(count * IW / 39)
        rect(bx, by, segw - 2, 14, color)
        bx += segw
    lab = " · ".join("%s %d" % (n, c) for n, c, _ in regions)
    draw_text_c(W // 2, 242, "sansb12", lab, INK)
    # heroes
    heroes = [
        (ill_kyiv, "1 · UKRAINE — WAR", "RUSSIA TEARS DOWN KYIV'S DNIPRO BRIDGES",
         "110+ missiles and some 400 drones strike the capital; "
         "at least 8 killed. (Reuters)"),
        (ill_cyclone, "2 · INDIA — CLIMATE", "CYCLONE AKVAN BATTERS THE ODISHA COAST",
         "Landfall near Gopalpur: winds over 90 km/h, 300,000+ evacuated, "
         "28 trains cancelled."),
        (ill_markets, "3 · ASIA — MARKETS", "AI SELL-OFF SINKS ASIA'S MARKETS",
         "Taipei −6.2% · Seoul −5.2% · Tokyo −4.9% · Hong Kong −2.4% "
         "as the tech rout deepens."),
    ]
    hy = 264
    for i, (ill, kick, head, body) in enumerate(heroes):
        hx = MX + i * (316 + 12)
        frame(hx, hy, 316, 180, INK, 1)
        ill(hx + 1, hy + 1, 314, 75)
        draw_text(hx + 10, hy + 82, "sansb11", kick, RED)
        draw_rich(hx + 10, hy + 98, [("sansb18", head, INK)], 296, 21,
                  max_lines=2)
        draw_rich(hx + 10, hy + 142, [("sans13", body, (56, 50, 44))], 296,
                  15, max_lines=2)
    # featured 4-13
    section_head(MX, 454, "MORE TOP STORIES")
    featured = [
        (4, "Russian missile falls in Poland",
         "NATO calls the cross-border strike a grave violation."),
        (5, "UK–EU reset deal sealed",
         "Brussels package includes 100,000 youth visas a year."),
        (6, "COP31 runs into overtime in Antalya",
         "The latest draft text drops the words 'fossil fuels'."),
        (7, "CGIL general strike grips Italy",
         "Walkouts and rallies in more than 100 cities. (Reuters)"),
        (8, "Ruling party moves on chief justice",
         "Impeachment of Chief Justice Cho Hee-dae adopted. (Yonhap)"),
        (9, "Iraqi army enters Hezbollah HQ",
         "Troops enter the Jurf al-Sakhar joint operations centre."),
        (10, "Kenya drills first oil well",
         "Amosing 1 spudded in Turkana — a first for Kenya."),
        (11, "Tanker ablaze near Hormuz",
         "Vessel hit by a projectile off the strait. (UKMTO)"),
        (12, "Senate blocks Iran war-powers vote",
         "The war-powers resolution falls 51–48 in Washington."),
        (13, "Phillips smashes 118 vs India",
         "Centuries in all three formats inside one year. (ICC)"),
    ]
    for idx, (num, head, body) in enumerate(featured):
        colx = MX if idx % 2 == 0 else 512
        colw = 460 if idx % 2 == 0 else 486
        rowy = 476 + (idx // 2) * 36
        rect(colx, rowy, 20, 20, RED)
        ns = str(num)
        draw_text(colx + 10 - textw("sansb13", ns) // 2, rowy + 3, "sansb13",
                  ns, WHITE)
        draw_text(colx + 28, rowy, "sansb14", head, INK)
        draw_text(colx + 28, rowy + 18, "sans12", body, (56, 50, 44))
    # band D headings
    section_head(MX, 662, "IN BRIEF — THE REST OF FRIDAY")
    section_head(658, 662, "WHERE IT HAPPENED")
    # one-liners 14-39
    briefs = [
        (14, "FRANCE CALLS UN TALKS", "Paris seeks an urgent Security Council meeting."),
        (15, "STUDENTS MARCH IN ±25 COUNTRIES", "Protests sweep Europe's campuses."),
        (16, "ESTONIA SHUTS RUSSIAN BORDER", "Frontier closes from 1 December."),
        (17, "UKRAINE GRID 'EXTREMELY CRITICAL'", "Operator's warning after the strikes."),
        (18, "LVIV STATION STRUCK", "Rail hub hit in western Ukraine."),
        (19, "MERZ: 'NO NEW YALTA'", "Chancellor rejects carving up Europe."),
        (20, "NIKKEI LOWEST SINCE APRIL", "Tokyo shares slide again."),
        (21, "CHINA HOLDS LPR, 18TH MONTH", "Rates steady at 3.0% and 3.5%."),
        (22, "SRI LANKA HIKES TO 9%", "Central bank tightens policy."),
        (23, "PAKISTAN RAID KILLS 22 MILITANTS", "Operation in Khyber Pakhtunkhwa."),
        (24, "S. KOREA CHOLERA CASE", "First case in 10 years confirmed."),
        (25, "SOFTBANK −14% IN TOKYO", "AI sell-off bites Japan's giant."),
        (26, "ISRAELI STRIKE KILLS 6 IN GAZA", "(AFP)"),
        (27, "SAUDI-LED COALITION IN HODEIDAH", "Operations reported in Yemen."),
        (28, "DRONE KILLS 10 AT SUDAN GOLD MINE", "Attack on a mining site."),
        (29, "GUNFIRE NEAR BADME", "Shots on the Ethiopia–Eritrea line."),
        (30, "ANTHROPIC −4.7% AFTER HOURS", "Post-IPO fade, $83 to $97.17."),
        (31, "S&P 500 −2.0%, SIXTH STRAIGHT LOSS", "Dow falls 1,101 points. (AP)"),
        (32, "THOUSANDS MARCH IN COLOMBIA", "Crowds fill the streets."),
        (33, "TWO SALVADORAN SOLDIERS DIE IN HAITI", "Mission deaths confirmed."),
        (34, "ASX 200 DOWN 1.6%", "Sydney follows the global slide."),
        (35, "NICHOLLS 175 AS NZ POST 368", "A big total against India."),
        (36, "IMF: WORLD DEBT NEARS 100% OF GDP", "The fund sounds the warning."),
        (37, "GLOBAL STOCKS EYE 7TH DAILY FALL", "The rout rolls on."),
        (38, "BRENT NEAR $92", "Oil holds firm amid the turmoil."),
        (39, "GOLD, SILVER FALL WITH STOCKS", "Precious metals join the sell-off."),
    ]
    for idx, (num, lead, rest) in enumerate(briefs):
        if idx < 13:
            colx, colw, row = MX, 292, idx
        else:
            colx, colw, row = 334, 312, idx - 13
        rowy = 684 + row * 25
        draw_text(colx, rowy, "sansb11", str(num), RED)
        draw_rich(colx + 22, rowy,
                  [("sansb11", lead + " — ", INK),
                   ("sans11", rest, (60, 55, 48))],
                  colw - 22, 12, max_lines=2)
    # map
    draw_map(658, 684, 340, 204)
    draw_text(658, 890, "sans11", "Pins 1–13 mark the first thirteen stories.",
              GRAY)
    # date check box
    dx, dy, dw = 658, 906, 340
    rect(dx, dy, dw, 112, (248, 236, 234))
    frame(dx, dy, dw, 112, RED, 2)
    rect(dx, dy, dw, 17, RED)
    draw_text(dx + 8, dy + 3, "sansb11", "DATE CHECK — NOT FRIDAY'S NEWS",
              WHITE)
    dc = ("HELD BACK AS THU 19 NOV NEWS: ICJ ruling on Myanmar/Rohingya "
          "genocide · Trump–Xi–Putin Shenzhen declaration · Bukele "
          "third-term filing · Tonga drought emergency · migrant boat lost "
          "off Senegal. NOT YET: final COP31 text · BepiColombo at Mercury. "
          "SOURCES: Reuters · AP · AFP · BBC · The Guardian · Al Jazeera · "
          "Yonhap · NHK")
    draw_rich(dx + 8, dy + 22, [("sans11", dc, INK)], dw - 16, 12,
              max_lines=7)


# ---------------------------------------------------------------- output ----

def save_png(path):
    raw = bytearray()
    stride = W * 3
    for yy in range(H):
        raw.append(0)
        raw += FB[yy * stride:(yy + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n" +
           chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)) +
           chunk(b"IDAT", comp) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    build_page()
    try:
        os.makedirs("/output", exist_ok=True)
        n = save_png("/output/entry.png")
        print("wrote /output/entry.png (%d bytes)" % n)
    except OSError:
        n = save_png("entry.png")
        print("wrote entry.png (%d bytes)" % n)


if __name__ == "__main__":
    main()
