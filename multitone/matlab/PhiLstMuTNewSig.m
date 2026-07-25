Dur = 1800;
Nch = 2;
AttVol = -0.25;
Rd = 'RD';
Ext = '.flac';
% 1a) PhiLstMuTNewMin[Nch 1][Frac 03][044100-24][00020-19845][Nfr 030][000223]-[ 8.3547]
% 1b) PhiLstMuTNewMin[Nch 1][Frac 03][044100-24][00020-19845][Nfr 030][005166]-[ 8.1785]
% 1c) PhiLstMuTNewMin[Nch 1][Frac 03][044100-24][00020-19845][Nfr 030][039251]-[ 8.0048] * 
% philstws = load('PhiLstMuTNewMin[Nch 1][Frac 03][044100-24][00020-19845][Nfr 030][039251]-[ 8.0048].mat');
% 2a) PhiLstMuTNewMin[Nch 1][Frac 03][048000-24][00020-21600][Nfr 030][000358]-[ 8.6017]
% 2b) PhiLstMuTNewMin[Nch 1][Frac 03][048000-24][00020-21600][Nfr 030][005348]-[ 8.1766]
% 2c) PhiLstMuTNewMin[Nch 1][Frac 03][048000-24][00020-21600][Nfr 030][001641]-[ 7.8952] *
% philstws = load('PhiLstMuTNewMin[Nch 1][Frac 03][048000-24][00020-21600][Nfr 030][001641]-[ 7.8952].mat');
% 3a) PhiLstMuTNewMin[Nch 1][Frac 03][088200-24][00020-39690][Nfr 034][000693]-[ 8.4310]
% 3b) PhiLstMuTNewMin[Nch 1][Frac 03][088200-24][00020-39690][Nfr 034][008362]-[ 8.0331] * 
% 3c) PhiLstMuTNewMin[Nch 1][Frac 03][088200-24][00020-39690][Nfr 034][068884]-[ 8.0680]
% philstws = load('PhiLstMuTNewMin[Nch 1][Frac 03][088200-24][00020-39690][Nfr 034][008362]-[ 8.0331].mat');
% 4a) PhiLstMuTNewMin[Nch 1][Frac 03][096000-24][00020-43200][Nfr 034][000813]-[ 8.3623]
% 4b) PhiLstMuTNewMin[Nch 1][Frac 03][096000-24][00020-43200][Nfr 034][009476]-[ 8.2422]
% 4c) PhiLstMuTNewMin[Nch 1][Frac 03][096000-24][00020-43200][Nfr 034][082164]-[ 8.2034] *
% philstws = load('PhiLstMuTNewMin[Nch 1][Frac 03][096000-24][00020-43200][Nfr 034][082164]-[ 8.2034].mat');
% 5a) PhiLstMuTNewMin[Nch 1][Frac 03][176400-24][00020-79380][Nfr 037][000653]-[ 8.6726]
% 5b) PhiLstMuTNewMin[Nch 1][Frac 03][176400-24][00020-79380][Nfr 037][009946]-[ 8.2350]
% 5c) PhiLstMuTNewMin[Nch 1][Frac 03][176400-24][00020-79380][Nfr 037][080970]-[ 8.1501] *
% philstws = load('PhiLstMuTNewMin[Nch 1][Frac 03][176400-24][00020-79380][Nfr 037][080970]-[ 8.1501].mat');
% 6a) PhiLstMuTNewMin[Nch 1][Frac 03][192000-24][00020-86400][Nfr 037][000056]-[ 8.5734]
% 6b) PhiLstMuTNewMin[Nch 1][Frac 03][192000-24][00020-86400][Nfr 037][005658]-[ 8.2837]
% 6c) PhiLstMuTNewMin[Nch 1][Frac 03][192000-24][00020-86400][Nfr 037][022727]-[ 7.9949] *
% philstws = load('PhiLstMuTNewMin[Nch 1][Frac 03][192000-24][00020-86400][Nfr 037][022727]-[ 7.9949].mat');
% 7a) PhiLstMuTNewMin[Nch 1][Frac 06][044100-24][00020-19845][Nfr 059][000748]-[ 8.7832]
% 7b) PhiLstMuTNewMin[Nch 1][Frac 06][044100-24][00020-19845][Nfr 059][001302]-[ 8.5281]
% 7c) PhiLstMuTNewMin[Nch 1][Frac 06][044100-24][00020-19845][Nfr 059][011021]-[ 8.1048] *
% philstws = load('PhiLstMuTNewMin[Nch 1][Frac 06][044100-24][00020-19845][Nfr 059][011021]-[ 8.1048].mat');
% 8a) PhiLstMuTNewMin[Nch 1][Frac 06][048000-24][00020-21600][Nfr 060][000797]-[ 8.4842]
% 8b) PhiLstMuTNewMin[Nch 1][Frac 06][048000-24][00020-21600][Nfr 060][009956]-[ 8.5813]
% 8c) PhiLstMuTNewMin[Nch 1][Frac 06][048000-24][00020-21600][Nfr 060][037254]-[ 8.2292] *
% philstws = load('PhiLstMuTNewMin[Nch 1][Frac 06][048000-24][00020-21600][Nfr 060][037254]-[ 8.2292].mat');
% 9a) PhiLstMuTNewMin[Nch 1][Frac 06][088200-24][00020-39690][Nfr 066][000435]-[ 8.8882]
% 9b) PhiLstMuTNewMin[Nch 1][Frac 06][088200-24][00020-39690][Nfr 066][002519]-[ 8.7722]
% 9c) PhiLstMuTNewMin[Nch 1][Frac 06][088200-24][00020-39690][Nfr 066][035748]-[ 8.2881] *
% philstws = load('PhiLstMuTNewMin[Nch 1][Frac 06][088200-24][00020-39690][Nfr 066][035748]-[ 8.2881].mat');
%10a) PhiLstMuTNewMin[Nch 1][Frac 06][096000-24][00020-43200][Nfr 066][000101]-[ 8.7912]
%10b) PhiLstMuTNewMin[Nch 1][Frac 06][096000-24][00020-43200][Nfr 066][008217]-[ 8.5826]
%10c) PhiLstMuTNewMin[Nch 1][Frac 06][096000-24][00020-43200][Nfr 066][056015]-[ 8.3781] *
% philstws = load('PhiLstMuTNewMin[Nch 1][Frac 06][096000-24][00020-43200][Nfr 066][056015]-[ 8.3781].mat');
%11a) PhiLstMuTNewMin[Nch 1][Frac 06][176400-24][00020-79380][Nfr 072][000685]-[ 8.4419]
%11b) PhiLstMuTNewMin[Nch 1][Frac 06][176400-24][00020-79380][Nfr 072][007847]-[ 8.6796]
%11c) PhiLstMuTNewMin[Nch 1][Frac 06][176400-24][00020-79380][Nfr 072][043202]-[ 8.4311] *
% philstws = load('PhiLstMuTNewMin[Nch 1][Frac 06][176400-24][00020-79380][Nfr 072][043202]-[ 8.4311].mat');
%12a) PhiLstMuTNewMin[Nch 1][Frac 06][192000-24][00020-86400][Nfr 072][000097]-[ 9.0907]
%12b) PhiLstMuTNewMin[Nch 1][Frac 06][192000-24][00020-86400][Nfr 072][003095]-[ 8.4417]
%12C) PhiLstMuTNewMin[Nch 1][Frac 06][192000-24][00020-86400][Nfr 072][042952]-[ 8.0254] *
%philstws = load('PhiLstMuTNewMin[Nch 1][Frac 06][192000-24][00020-86400][Nfr 072][042952]-[ 8.0254].mat');
%13a) PhiLstMuTNewMin[Nch 1][Frac 12][044100-24][00020-19845][Nfr 106][000600]-[ 8.9653]
%13b) PhiLstMuTNewMin[Nch 1][Frac 12][044100-24][00020-19845][Nfr 106][009857]-[ 9.0825]
%13c) PhiLstMuTNewMin[Nch 1][Frac 12][044100-24][00020-19845][Nfr 106][094121]-[ 8.6789] *
% philstws = load('PhiLstMuTNewMin[Nch 1][Frac 12][044100-24][00020-19845][Nfr 106][094121]-[ 8.6789].mat');
%14a) PhiLstMuTNewMin[Nch 1][Frac 12][048000-24][00020-21600][Nfr 109][000193]-[ 9.3747]
%14b) PhiLstMuTNewMin[Nch 1][Frac 12][048000-24][00020-21600][Nfr 109][009442]-[ 9.1191]
%14c) PhiLstMuTNewMin[Nch 1][Frac 12][048000-24][00020-21600][Nfr 109][008256]-[ 8.7888] *
% philstws = load('PhiLstMuTNewMin[Nch 1][Frac 12][048000-24][00020-21600][Nfr 109][008256]-[ 8.7888].mat');
%15a) PhiLstMuTNewMin[Nch 1][Frac 12][088200-24][00020-39690][Nfr 121][000187]-[ 9.5864]
%15b) PhiLstMuTNewMin[Nch 1][Frac 12][088200-24][00020-39690][Nfr 121][000161]-[ 8.8859] *
%15c) PhiLstMuTNewMin[Nch 1][Frac 12][088200-24][00020-39690][Nfr 121][086225]-[ 9.0150]
% philstws = load('PhiLstMuTNewMin[Nch 1][Frac 12][088200-24][00020-39690][Nfr 121][000161]-[ 8.8859].mat');
%16a) PhiLstMuTNewMin[Nch 1][Frac 12][096000-24][00020-43200][Nfr 121][000411]-[ 9.4378]
%16b) PhiLstMuTNewMin[Nch 1][Frac 12][096000-24][00020-43200][Nfr 121][005546]-[ 9.0956]
%16c) PhiLstMuTNewMin[Nch 1][Frac 12][096000-24][00020-43200][Nfr 121][066838]-[ 8.7105] *
% philstws = load('PhiLstMuTNewMin[Nch 1][Frac 12][096000-24][00020-43200][Nfr 121][066838]-[ 8.7105].mat');
%17a) PhiLstMuTNewMin[Nch 1][Frac 12][176400-24][00020-79380][Nfr 131][000908]-[ 9.3406]
%17b) PhiLstMuTNewMin[Nch 1][Frac 12][176400-24][00020-79380][Nfr 131][009503]-[ 9.1084]
%17c) PhiLstMuTNewMin[Nch 1][Frac 12][176400-24][00020-79380][Nfr 131][077467]-[ 8.7907] *
% philstws = load('PhiLstMuTNewMin[Nch 1][Frac 12][176400-24][00020-79380][Nfr 131][077467]-[ 8.7907].mat');
%18a) PhiLstMuTNewMin[Nch 1][Frac 12][192000-24][00020-86400][Nfr 133][000372]-[ 9.4387]
%18b) PhiLstMuTNewMin[Nch 1][Frac 12][192000-24][00020-86400][Nfr 133][009772]-[ 9.2193]
%18c) PhiLstMuTNewMin[Nch 1][Frac 12][192000-24][00020-86400][Nfr 133][028791]-[ 8.9109] *
%%%%) philstws = load('PhiLstMuTNewMin[Nch 1][Frac 12][192000-24][00020-86400][Nfr 133][028791]-[ 8.9109].mat');

% LFL 1) philstws = load('PhiLstMuTNewMin[Nch 1][Frac 03][LFL 043][044100-24][00020-19845][Nfr 027][005133]-[ 8.6262].mat');
% LFL 2) philstws = load('PhiLstMuTNewMin[Nch 1][Frac 03][LFL 043][048000-24][00020-21600][Nfr 027][049062]-[ 8.5905].mat');
% LFL 3) philstws = load('PhiLstMuTNewMin[Nch 1][Frac 03][LFL 043][044100-24][00020-19845][Nfr 027][042525]-[ 8.6138].mat');
philstws = load('PhiLstMuTNewMin[Nch 1][Frac 03][LFL 043][048000-24][00020-21600][Nfr 027][060159]-[ 8.4655].mat');

frqprilen = length(philstws.FrqPriLst);
fllow = philstws.FrqPriLst(1);
flhig = philstws.FrqPriLst(frqprilen);
Fraction = philstws.Fraction;
Fsam = philstws.Fsam;
% attenuation vector
if Fraction == 3
    load('fr03pri384k.mat');
    if Fsam == 44100
        FrqPriLst = fr03frqprilim044k(:,1);
        FrqAttLst = fr03frqprilim044k(:,2);
    elseif Fsam == 48000
        FrqPriLst = fr03frqprilim048k(:,1);
        FrqAttLst = fr03frqprilim048k(:,2);
    elseif Fsam == 88200
        FrqPriLst = fr03frqprilim088k(:,1);
        FrqAttLst = fr03frqprilim088k(:,2);
    elseif Fsam == 96000
        FrqPriLst = fr03frqprilim096k(:,1);
        FrqAttLst = fr03frqprilim096k(:,2);
    elseif Fsam == 176400
        FrqPriLst = fr03frqprilim176k(:,1);
        FrqAttLst = fr03frqprilim176k(:,2);
    elseif Fsam == 192000
        FrqPriLst = fr03frqprilim192k(:,1);
        FrqAttLst = fr03frqprilim192k(:,2);
    end
elseif Fraction == 6
    load('fr06pri384k.mat');
    if Fsam == 44100
        FrqPriLst = fr06frqprilim044k(:,1);
        FrqAttLst = fr06frqprilim044k(:,2);
    elseif Fsam == 48000
        FrqPriLst = fr06frqprilim048k(:,1);
        FrqAttLst = fr06frqprilim048k(:,2);
    elseif Fsam == 88200
        FrqPriLst = fr06frqprilim088k(:,1);
        FrqAttLst = fr06frqprilim088k(:,2);
    elseif Fsam == 96000
        FrqPriLst = fr06frqprilim096k(:,1);
        FrqAttLst = fr06frqprilim096k(:,2);
    elseif Fsam == 176400
        FrqPriLst = fr06frqprilim176k(:,1);
        FrqAttLst = fr06frqprilim176k(:,2);
    elseif Fsam == 192000
        FrqPriLst = fr06frqprilim192k(:,1);
        FrqAttLst = fr06frqprilim192k(:,2);
    end
elseif Fraction == 12
    load('fr12pri384k.mat');
    if Fsam == 44100
        FrqPriLst = fr12frqprilim044k(:,1);
        FrqAttLst = fr12frqprilim044k(:,2);
    elseif Fsam == 48000
        FrqPriLst = fr12frqprilim048k(:,1);
        FrqAttLst = fr12frqprilim048k(:,2);
    elseif Fsam == 88200
        FrqPriLst = fr12frqprilim088k(:,1);
        FrqAttLst = fr12frqprilim088k(:,2);
    elseif Fsam == 96000
        FrqPriLst = fr12frqprilim096k(:,1);
        FrqAttLst = fr12frqprilim096k(:,2);
    elseif Fsam == 176400
        FrqPriLst = fr12frqprilim176k(:,1);
        FrqAttLst = fr12frqprilim176k(:,2);
    elseif Fsam == 192000
        FrqPriLst = fr12frqprilim192k(:,1);
        FrqAttLst = fr12frqprilim192k(:,2);
    else
        return
    end
end
Sbit = philstws.Sbit;
CFact0 = philstws.cfact0;
[ycd,FrqLst,PhiLst,VolLst,AttVol,Rd,Dur,Frs,Sab,NCh] = FrqLstVolAtt(philstws.FrqPriLst,philstws.PhiLst,FrqAttLst,AttVol,Rd,Dur,Fsam,Sbit,Nch);
FileNam = 'PrimeToneNewPhi[Nch %1d][Frac %3d][%05d-%05d][Nfr %3d]-[%d-%d]-[%ds]-[%5.2fdB]-[%7.4f]';
cfact = 20.0 .* log10(peak2rms(double(ycd)./ double(2^32)));
fprintf('cfact: L: %10.4f R: %10.4f\n',cfact(1), cfact(2));
% plot(double(ycd)./ double(2^32),'DisplayName','ycdn')
FileName = compose(FileNam,[Nch,Fraction,fllow,flhig,frqprilen,Fsam,Sbit,Dur,AttVol,CFact0(1)]);
FileName = strcat(FileName,'-[');
FileName = strcat(FileName,Rd);
FileName = strcat(FileName,']');
FileName = strcat(FileName,Ext);
audiowrite(string(FileName),ycd,Frs,'BitsPerSample',Sab);