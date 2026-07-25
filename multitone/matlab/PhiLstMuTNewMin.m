% iteration limits
MaxIter = 100000;
LastBestIter = 1;
MaxIter = MaxIter + LastBestIter - 1;
% duration in seconds
Dur = 1;
% sampling frequency in Hz
Fsam = 96000;
% quantization bits
Sbit = 24;
% channel number
Nch = 1;
% peak level attenuation
AttVol = -0.25;
% octave subdivisions
Fraction = 12;
% Initial Low Frequency Index:
% 1,2,3,4 -> 19,23,31,43 (Hz)
iLowFreq = 4;
% rounding function in use
Rd = 'RD';
% audio file type : wav/flac
Ext = '.flac';
% lower frequency limit
fllow=20;
% high frequency limit; max flhig = round(Fsam./2);
flhig=Fsam./2.0;
flhig=flhig-0.1.*flhig;
% crest factor: initialization to maximum acceptable value to begin with
cfact0 = zeros(1,Nch);
for j=1:Nch
    cfact0(j) = 18.0;
end
% List of multitone frequencies within extremes
[frqlst,frqpri,frqlen,frqprilen] = MuTPrimes(Fraction,fllow,flhig);
% attenuation vs. frequency
if Fraction == 3
    load('fr03pri384k.mat');
    if Fsam == 44100
        lll = length(fr03frqprilim044k);
        FrqPriLst = fr03frqprilim044k(iLowFreq:lll,1);
        FrqAttLst = fr03frqprilim044k(iLowFreq:lll,2)+fr03frqprilim044k(iLowFreq:iLowFreq,2);
    elseif Fsam == 48000
        lll = length(fr03frqprilim048k);
        FrqPriLst = fr03frqprilim048k(iLowFreq:lll,1);
        FrqAttLst = fr03frqprilim048k(iLowFreq:lll,2)+fr03frqprilim044k(iLowFreq:iLowFreq,2);
    elseif Fsam == 88200
        lll = length(fr03frqprilim088k);
        FrqPriLst = fr03frqprilim088k(iLowFreq:lll,1);
        FrqAttLst = fr03frqprilim088k(iLowFreq:lll,2);
    elseif Fsam == 96000
        lll = length(fr03frqprilim096k);
        FrqPriLst = fr03frqprilim096k(iLowFreq:lll,1);
        FrqAttLst = fr03frqprilim096k(iLowFreq:lll,2);
    elseif Fsam == 176400
        lll = length(fr03frqprilim176k);
        FrqPriLst = fr03frqprilim176k(iLowFreq:lll,1);
        FrqAttLst = fr03frqprilim176k(iLowFreq:lll,2);
    elseif Fsam == 192000
        lll = length(fr03frqprilim192k);
        FrqPriLst = fr03frqprilim192k(iLowFreq:lll,1);
        FrqAttLst = fr03frqprilim192k(iLowFreq:lll,2);
    end
elseif Fraction == 6
    load('fr06pri384k.mat');
    if Fsam == 44100
        lll = length(fr06frqprilim044k);
        FrqPriLst = fr06frqprilim044k(iLowFreq:lll,1);
        FrqAttLst = fr06frqprilim044k(iLowFreq:lll,2);
    elseif Fsam == 48000
        lll = length(fr06frqprilim048k);
        FrqPriLst = fr06frqprilim048k(iLowFreq:lll,1);
        FrqAttLst = fr06frqprilim048k(iLowFreq:lll,2);
    elseif Fsam == 88200
        lll = length(fr06frqprilim088k);
        FrqPriLst = fr06frqprilim088k(iLowFreq:lll,1);
        FrqAttLst = fr06frqprilim088k(iLowFreq:lll,2);
    elseif Fsam == 96000
        lll = length(fr06frqprilim096k);
        FrqPriLst = fr06frqprilim096k(iLowFreq:lll,1);
        FrqAttLst = fr06frqprilim096k(iLowFreq:lll,2);
    elseif Fsam == 176400
        lll = length(fr06frqprilim176k);
        FrqPriLst = fr06frqprilim176k(iLowFreq:lll,1);
        FrqAttLst = fr06frqprilim176k(iLowFreq:lll,2);
    elseif Fsam == 192000
        lll = length(fr06frqprilim192k);
        FrqPriLst = fr06frqprilim192k(iLowFreq:lll,1);
        FrqAttLst = fr06frqprilim192k(iLowFreq:lll,2);
    end
elseif Fraction == 12
    load('fr12pri384k.mat');
    if Fsam == 44100
        lll = length(fr12frqprilim044k);
        FrqPriLst = fr12frqprilim044k(iLowFreq:lll,1);
        FrqAttLst = fr12frqprilim044k(iLowFreq:lll,2);
    elseif Fsam == 48000
        lll = length(fr12frqprilim048k);
        FrqPriLst = fr12frqprilim048k(iLowFreq:lll,1);
        FrqAttLst = fr12frqprilim048k(iLowFreq:lll,2);
    elseif Fsam == 88200
        lll = length(fr12frqprilim088k);
        FrqPriLst = fr12frqprilim088k(iLowFreq:lll,1);
        FrqAttLst = fr12frqprilim088k(iLowFreq:lll,2);
    elseif Fsam == 96000
        lll = length(fr12frqprilim096k);
        FrqPriLst = fr12frqprilim096k(iLowFreq:lll,1);
        FrqAttLst = fr12frqprilim096k(iLowFreq:lll,2);
    elseif Fsam == 176400
        lll = length(fr12frqprilim176k);
        FrqPriLst = fr12frqprilim176k(iLowFreq:lll,1);
        FrqAttLst = fr12frqprilim176k(iLowFreq:lll,2);
    elseif Fsam == 192000
        lll = length(fr12frqprilim192k);
        FrqPriLst = fr12frqprilim192k(iLowFreq:lll,1);
        FrqAttLst = fr12frqprilim192k(iLowFreq:lll,2);
    else
        return
    end
end
FrqPriLen = length(FrqPriLst);
% phase vector: file name format
FilePhi = 'PhiLstMuTNewMin[Nch %1d][Frac %02d][LFL %03d][%06d-%02d][%05d-%05d][Nfr %03d][%06d]-[%7.4f]';
% FilePhi = 'PhiLstMuTMinimize[%05d-%05d][%06d]-[%7.4f]';
% waveform: file name format
FileNam = 'PrimeToneNewPhi[Nch %1d][Frac %02d][LFL %03d][%05d-%05d][Nfr %03d]-[%0d-%0d]-[%ds]-[%5.2fdB]-[%06d]-[%7.4f]';
% iteration to find a lower crest factor
for i = LastBestIter:MaxIter
    rng('shuffle');
    PhiLst=rand(FrqPriLen,1) .* pi;
    [ycd,FrqLst,PhiLst,VolLst,AttVol,Rd,Dur,Frs,Sab,NCh] = FrqLstVolAtt(FrqPriLst,PhiLst,FrqAttLst,AttVol,Rd,Dur,Fsam,Sbit,Nch);
    cfact = 20.0 .* log10(peak2rms(double(ycd)./ double(2^32)));
    fprintf('cfact0: Ch1: %10.4f -> cfact: Ch1: %10.4f\n',cfact0(1), cfact(1));
    if cfact(1) < cfact0(1)
        for j=1:Nch
            cfact0(j) = cfact(j);
        end
        FilePhiMin = compose(FilePhi,[Nch,Fraction,FrqPriLst(1:1,1),Fsam,Sbit,fllow,flhig,FrqPriLen,i,cfact0(1)]);
        FilePhiMin = strcat(FilePhiMin, '.mat');
        save(char(FilePhiMin), 'Fraction','iLowFreq', 'Fsam', 'Sbit', 'FrqPriLst', 'PhiLst', 'cfact0')
        % plot(double(ycd)./ double(2^32),'DisplayName','ycdn')
        FileName = compose(FileNam,[Nch,Fraction,FrqPriLst(1:1,1),fllow,flhig,FrqPriLen,Fsam,Sbit,Dur,AttVol,i,cfact0(1)]);
        FileName = strcat(FileName,'-[');
        FileName = strcat(FileName,Rd);
        FileName = strcat(FileName,']');
        FileName = strcat(FileName,Ext);
        audiowrite(string(FileName),ycd,Frs,'BitsPerSample',Sab);
    end
end