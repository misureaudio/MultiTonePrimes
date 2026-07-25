function [frqlst,frqprilim,frqlen,frqprilen] = MuTPrimes(fraction,frqlimlow,frqlimhig)
[frqlst, frqlen]=FrqOctFraction(4,18,fraction);
frqlst=frqlst';
frqpri=zeros(frqlen,1);
for i = 1:frqlen
    frqpri(i)=max(primes(frqlst(i)));
end
frqpriuni = unique(frqpri);
frqprilim = frqpriuni(frqpriuni < frqlimhig);
frqprilim = frqprilim(frqprilim > frqlimlow);
frqprilen = length(frqprilim);