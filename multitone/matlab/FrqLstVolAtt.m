function [ycd,FrqLst,PhiLst,VolLst,VolAtt,Rounded,Dur,Frs,Sab,NCh] = FrqLstVolAtt(FrqLst,PhiLst,VolLst,VolAtt,Rounded,Dur,Frs,Sab,NCh)
if (Frs  ~= 44100 && Frs ~= 48000 && Frs ~= 88200 && Frs ~= 96000 && Frs ~= 176400 && Frs ~= 192000)
    Frs=44100;
end
if (Sab ~= 16 && Sab ~= 24 && Sab ~= 32)
    Sab=24;
end
if not(strcmp(Rounded,'RD'))
    Rounded = 'NO';
end
lenv = Frs * Dur;
% **** ? **** vs = power(10, Vol ./ 20) .* 2 .^ Sab;
% vs = power(10, VolAtt ./ 20) .* 2 .^ Sab;
ycd = zeros(lenv,NCh);
twopi = 2 .* pi;
phinr = 360 ./ twopi;
fprintf('>');
for k = 1:length(FrqLst)
    vs = power(10, VolLst(k) ./ 20);
    fprintf( 'frq: %5ld phi: %6.2f\n',int32(FrqLst(k)), PhiLst(k) .* phinr);
    for i=1:lenv
        y = cos(twopi.*(i-1).* FrqLst(k)./Frs + PhiLst(k));
        for j=1:NCh
            ycd(i,j) = ycd(i,j) + y .* vs;
        end
    end
    fprintf('>');
end
fprintf('\n');
vs = power(10, VolAtt ./ 20);
if Sab == 16 || Sab == 24
    scale = 2 .^ Sab;
    scalediv2 = scale ./ 2 - 1;
    ycdmax = max(abs(ycd));
    ycd = ycd ./ ycdmax;
    ycd = ycd .* scalediv2 .* vs;
else
    ycdmax = max(abs(ycd));
    ycd = ycd ./ ycdmax .* vs;
end
if Sab == 16
    if strcmp(Rounded,'RD')
        fprintf('%5.2f %2s\n',VolAtt,'RD');
        ycd=int16(round(ycd));
    else
        fprintf('%5.2f %2s\n',VolAtt,'NO');
        ycd=int16(ycd);
    end
else
    if Sab == 24
        if strcmp(Rounded,'RD')
            fprintf('%5.2f %2s\n',VolAtt,'RD');
            ycd = int32(round(ycd) .* 256);
        else
            fprintf('%5.2f %2s\n',VolAtt,'NO');
            ycd = int32(ycd .* 256);
        end
    else
        if Sab == 32
            % ycd;
        end
    end
end
end