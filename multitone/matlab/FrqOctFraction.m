function [FrqLst, FrqLstLen] = FrqOctFraction(oct0,oct1,Fraction)
FrqLstLen = (oct1 - oct0 + 1) .* Fraction;
FrqLst = zeros(1,FrqLstLen);
k = 1;
for i = oct0:oct1
    % f = 0;
    for j = 1:Fraction
        f = 2 .^ i + (2 .^ (i+1) - 2 .^i)./Fraction .*(j-1);
        FrqLst(1,k) = round(f);
        k = k + 1;
    end
end
return