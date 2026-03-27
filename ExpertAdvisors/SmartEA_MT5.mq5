//+------------------------------------------------------------------+
//|                                              SmartEA_MT5.mq5     |
//|                         CryptoRobot Expert Advisor - MT5         |
//|                                                                  |
//|  Stratégie : Pullback sur tendance EMA + filtre RSI + ADX        |
//|  - Entrée à la clôture de bougie sur pullback en tendance        |
//|  - Stop Loss et Take Profit basés sur ATR                        |
//|  - Trailing Stop ATR automatique                                 |
//|  - Risque fixe en % du capital par trade                         |
//|  - Protection drawdown max                                       |
//|  - Arrêt automatique si 6 mois consécutifs en perte              |
//+------------------------------------------------------------------+
#property copyright "CryptoRobot"
#property link      ""
#property version   "1.00"
#property description "SmartEA - Pullback Tendance | EMA + RSI + ADX | Gestion risque ATR"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

//====================================================================
//  PARAMÈTRES D'ENTRÉE
//====================================================================

input string s1 = "======== STRATÉGIE ========";  // ──────────────
input int    EMA_Rapide    = 8;    // Période EMA rapide (signal)
input int    EMA_Lente     = 21;   // Période EMA lente (signal)
input int    EMA_Tendance  = 200;  // Période EMA tendance long terme
input int    RSI_Periode   = 14;   // Période RSI
input double RSI_Survente  = 40;   // RSI zone survente (signal achat)
input double RSI_Surachat  = 60;   // RSI zone surachat (signal vente)
input int    ADX_Periode   = 14;   // Période ADX
input double ADX_Min       = 22;   // ADX minimum requis (tendance confirmée)

input string s2 = "======= GESTION RISQUE =======";  // ──────────────
input double RisquePercent    = 1.0;  // Risque par trade en % du capital
input int    ATR_Periode      = 14;   // Période ATR
input double ATR_Mult_SL      = 1.5;  // Multiplicateur ATR pour Stop Loss
input double ATR_Mult_TP      = 3.0;  // Multiplicateur ATR pour Take Profit
input bool   UtiliserTrailing  = true; // Activer le Trailing Stop
input double ATR_Mult_Trail   = 1.2;  // Multiplicateur ATR pour Trailing Stop
input ulong  Deviation        = 10;   // Déviation maximale (points)

input string s3 = "======= PROTECTION ========";  // ──────────────
input double DrawdownMaxPct   = 15.0; // Drawdown max avant arrêt d'urgence (%)
input int    PertesConsecMax  = 6;    // Pertes consécutives max avant pause
input bool   Protection6Mois  = true; // Activer la protection 6 mois perdants
input bool   FiltreHeures     = true; // Filtrer les heures de trading
input int    HeureDebut       = 2;    // Heure début trading (serveur)
input int    HeureFin         = 22;   // Heure fin trading (serveur)

input string s4 = "======== GÉNÉRAL =========";  // ──────────────
input ulong  MagicNumber  = 20240101; // Numéro magique unique de l'EA
input string Commentaire  = "SmartEA"; // Commentaire sur les ordres

//====================================================================
//  VARIABLES GLOBALES
//====================================================================

CTrade         g_trade;
CPositionInfo  g_position;

double g_balancePic        = 0;
double g_balanceDebutMois  = 0;
int    g_pertesConsec      = 0;
int    g_moisSuivi         = 0;
double g_perfMensuelle[6];
bool   g_eaArrete          = false;
string g_raisonArret       = "";
ulong  g_dernierDealVerif  = 0;

// Handles d'indicateurs
int g_handleEmaR  = INVALID_HANDLE;
int g_handleEmaL  = INVALID_HANDLE;
int g_handleEmaT  = INVALID_HANDLE;
int g_handleRSI   = INVALID_HANDLE;
int g_handleADX   = INVALID_HANDLE;
int g_handleATR   = INVALID_HANDLE;

//====================================================================
//  INITIALISATION
//====================================================================

int OnInit()
{
   // Configurer l'objet de trading
   g_trade.SetExpertMagicNumber(MagicNumber);
   g_trade.SetDeviationInPoints(Deviation);
   g_trade.SetTypeFilling(ORDER_FILLING_FOK);

   // Créer les handles d'indicateurs
   g_handleEmaR = iMA(_Symbol, PERIOD_CURRENT, EMA_Rapide,   0, MODE_EMA, PRICE_CLOSE);
   g_handleEmaL = iMA(_Symbol, PERIOD_CURRENT, EMA_Lente,    0, MODE_EMA, PRICE_CLOSE);
   g_handleEmaT = iMA(_Symbol, PERIOD_CURRENT, EMA_Tendance, 0, MODE_EMA, PRICE_CLOSE);
   g_handleRSI  = iRSI(_Symbol, PERIOD_CURRENT, RSI_Periode, PRICE_CLOSE);
   g_handleADX  = iADX(_Symbol, PERIOD_CURRENT, ADX_Periode);
   g_handleATR  = iATR(_Symbol, PERIOD_CURRENT, ATR_Periode);

   if(g_handleEmaR == INVALID_HANDLE || g_handleEmaL == INVALID_HANDLE ||
      g_handleEmaT == INVALID_HANDLE || g_handleRSI  == INVALID_HANDLE ||
      g_handleADX  == INVALID_HANDLE || g_handleATR  == INVALID_HANDLE)
   {
      Print("Erreur : impossible de créer les handles d'indicateurs");
      return(INIT_FAILED);
   }

   // Initialisation des variables de protection
   g_balancePic       = AccountInfoDouble(ACCOUNT_BALANCE);
   g_balanceDebutMois = AccountInfoDouble(ACCOUNT_BALANCE);
   g_moisSuivi        = (int)TimeMonth(TimeCurrent());
   g_pertesConsec     = 0;
   g_eaArrete         = false;
   ArrayInitialize(g_perfMensuelle, 1.0);

   Print("=== SmartEA MT5 démarré ===");
   Print("Capital : ", AccountInfoDouble(ACCOUNT_BALANCE), " ",
         AccountInfoString(ACCOUNT_CURRENCY));
   Print("Risque par trade : ", RisquePercent, "%");
   Print("DrawdownMax : ", DrawdownMaxPct, "%");
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   // Libérer les handles
   if(g_handleEmaR != INVALID_HANDLE) IndicatorRelease(g_handleEmaR);
   if(g_handleEmaL != INVALID_HANDLE) IndicatorRelease(g_handleEmaL);
   if(g_handleEmaT != INVALID_HANDLE) IndicatorRelease(g_handleEmaT);
   if(g_handleRSI  != INVALID_HANDLE) IndicatorRelease(g_handleRSI);
   if(g_handleADX  != INVALID_HANDLE) IndicatorRelease(g_handleADX);
   if(g_handleATR  != INVALID_HANDLE) IndicatorRelease(g_handleATR);

   Comment("");
   Print("=== SmartEA MT5 arrêté (code ", reason, ") ===");
}

//====================================================================
//  TICK PRINCIPAL
//====================================================================

void OnTick()
{
   AfficherStatut();
   if(g_eaArrete) return;

   // Mise à jour du pic de balance
   double balActuelle = AccountInfoDouble(ACCOUNT_BALANCE);
   if(balActuelle > g_balancePic)
      g_balancePic = balActuelle;

   // Vérifications de protection
   if(VerifierDrawdown())     return;
   if(VerifierMois())         return;
   if(VerifierPertesConsec()) return;

   // Filtre horaire
   if(FiltreHeures && !HeureTradingOK()) return;

   // N'agir qu'à la clôture d'une nouvelle bougie
   static datetime derniereBarreTraitee = 0;
   datetime tempsBarre = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(tempsBarre == derniereBarreTraitee) return;
   derniereBarreTraitee = tempsBarre;

   // Gestion du trailing stop
   if(UtiliserTrailing)
      GererTrailingStop();

   // Chercher une entrée si aucune position
   if(CompterPositions() == 0)
      ChercherEntrees();
}

//====================================================================
//  ÉVÉNEMENT TRADE (pour détecter les trades fermés)
//====================================================================

void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest     &request,
                        const MqlTradeResult      &result)
{
   // On ne s'intéresse qu'aux deals exécutés en sortie de position
   if(trans.type != TRADE_TRANSACTION_DEAL_ADD) return;

   ulong dealTicket = trans.deal;
   if(dealTicket == 0 || dealTicket == g_dernierDealVerif) return;

   if(HistoryDealSelect(dealTicket))
   {
      long magic = HistoryDealGetInteger(dealTicket, DEAL_MAGIC);
      if(magic != (long)MagicNumber) return;

      ENUM_DEAL_ENTRY entry = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(dealTicket, DEAL_ENTRY);
      if(entry != DEAL_ENTRY_OUT && entry != DEAL_ENTRY_OUT_BY) return; // Seulement les clôtures

      g_dernierDealVerif = dealTicket;

      double profit = HistoryDealGetDouble(dealTicket, DEAL_PROFIT)
                    + HistoryDealGetDouble(dealTicket, DEAL_SWAP)
                    + HistoryDealGetDouble(dealTicket, DEAL_COMMISSION);

      if(profit < 0)
         g_pertesConsec++;
      else
         g_pertesConsec = 0;

      Print(StringFormat("[SmartEA] Deal #%llu fermé – Profit: %.2f | PertesConsec: %d",
                         dealTicket, profit, g_pertesConsec));
   }
}

//====================================================================
//  LOGIQUE D'ENTRÉE
//====================================================================

void ChercherEntrees()
{
   // Lire les valeurs sur la bougie FERMÉE (index 1)
   double emaRBuf[2], emaLBuf[2], emaTBuf[1], rsiBuf[1], adxBuf[1], atrBuf[1];

   if(CopyBuffer(g_handleEmaR, 0, 1, 2, emaRBuf) < 2) return;
   if(CopyBuffer(g_handleEmaL, 0, 1, 2, emaLBuf) < 2) return;
   if(CopyBuffer(g_handleEmaT, 0, 1, 1, emaTBuf) < 1) return;
   if(CopyBuffer(g_handleRSI,  0, 1, 1, rsiBuf)  < 1) return;
   if(CopyBuffer(g_handleADX,  0, 1, 1, adxBuf)  < 1) return;
   if(CopyBuffer(g_handleATR,  0, 1, 1, atrBuf)  < 1) return;

   // Index 0 = bougie fermée, index 1 = bougie précédente
   double emaR      = emaRBuf[0];
   double emaL      = emaLBuf[0];
   double emaRPrev  = emaRBuf[1];
   double emaLPrev  = emaLBuf[1];
   double emaT      = emaTBuf[0];
   double rsi       = rsiBuf[0];
   double adx       = adxBuf[0];
   double atr       = atrBuf[0];

   if(adx < ADX_Min) return;
   if(atr <= 0)      return;

   // Prix actuels
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

   // Prix de clôture de la dernière bougie fermée
   double closePrev = iClose(_Symbol, PERIOD_CURRENT, 1);

   //------------------------------------------------------------------
   //  SIGNAL ACHAT
   //------------------------------------------------------------------
   bool croisHaussier = (emaRPrev <= emaLPrev) && (emaR > emaL);
   bool pullbackAchat = (emaR > emaL) && (rsi >= RSI_Survente - 5) && (rsi <= RSI_Survente + 10);
   bool condAchat = (closePrev > emaT) &&
                    (croisHaussier || pullbackAchat) &&
                    (rsi > 30) && (rsi < 55);

   //------------------------------------------------------------------
   //  SIGNAL VENTE
   //------------------------------------------------------------------
   bool croisBaissier = (emaRPrev >= emaLPrev) && (emaR < emaL);
   bool pullbackVente  = (emaR < emaL) && (rsi <= RSI_Surachat + 5) && (rsi >= RSI_Surachat - 10);
   bool condVente = (closePrev < emaT) &&
                    (croisBaissier || pullbackVente) &&
                    (rsi < 70) && (rsi > 45);

   //------------------------------------------------------------------
   //  OUVERTURE DES ORDRES
   //------------------------------------------------------------------
   if(condAchat)
   {
      double sl   = NormaliserPrix(ask - ATR_Mult_SL * atr);
      double tp   = NormaliserPrix(ask + ATR_Mult_TP * atr);
      double lots = CalculerLots(ask - sl);
      if(lots <= 0) return;

      if(g_trade.Buy(lots, _Symbol, ask, sl, tp, Commentaire))
         Print("ACHAT ouvert | Lots:", lots, " | SL:", sl, " | TP:", tp);
      else
         Print("Erreur ACHAT: ", g_trade.ResultRetcode(), " – ", g_trade.ResultRetcodeDescription());
   }
   else if(condVente)
   {
      double sl   = NormaliserPrix(bid + ATR_Mult_SL * atr);
      double tp   = NormaliserPrix(bid - ATR_Mult_TP * atr);
      double lots = CalculerLots(sl - bid);
      if(lots <= 0) return;

      if(g_trade.Sell(lots, _Symbol, bid, sl, tp, Commentaire))
         Print("VENTE ouverte | Lots:", lots, " | SL:", sl, " | TP:", tp);
      else
         Print("Erreur VENTE: ", g_trade.ResultRetcode(), " – ", g_trade.ResultRetcodeDescription());
   }
}

//====================================================================
//  TRAILING STOP ATR
//====================================================================

void GererTrailingStop()
{
   double atrBuf[1];
   if(CopyBuffer(g_handleATR, 0, 1, 1, atrBuf) < 1) return;
   double atr = atrBuf[0];
   if(atr <= 0) return;

   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(!g_position.SelectByIndex(i))        continue;
      if(g_position.Magic()  != MagicNumber)  continue;
      if(g_position.Symbol() != _Symbol)      continue;

      double slActuel    = g_position.StopLoss();
      double prixOuvert  = g_position.PriceOpen();
      double nouveauSL;

      if(g_position.PositionType() == POSITION_TYPE_BUY)
      {
         nouveauSL = NormaliserPrix(bid - ATR_Mult_Trail * atr);
         if(nouveauSL > slActuel + _Point && bid > prixOuvert)
            g_trade.PositionModify(g_position.Ticket(), nouveauSL, g_position.TakeProfit());
      }
      else if(g_position.PositionType() == POSITION_TYPE_SELL)
      {
         nouveauSL = NormaliserPrix(ask + ATR_Mult_Trail * atr);
         if((slActuel == 0 || nouveauSL < slActuel - _Point) && ask < prixOuvert)
            g_trade.PositionModify(g_position.Ticket(), nouveauSL, g_position.TakeProfit());
      }
   }
}

//====================================================================
//  CALCUL DE LA TAILLE DE POSITION (RISK % FIXE)
//====================================================================

double CalculerLots(double distanceSL)
{
   if(distanceSL <= 0) return 0;

   double balance       = AccountInfoDouble(ACCOUNT_BALANCE);
   double risqueMontant = balance * (RisquePercent / 100.0);

   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);

   if(tickValue <= 0 || tickSize <= 0) return 0;

   double nbTicks = distanceSL / tickSize;
   double lots    = risqueMontant / (nbTicks * tickValue);

   // Normalisation selon contraintes broker
   double lotsMin  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double lotsMax  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double lotsStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);

   lots = MathFloor(lots / lotsStep) * lotsStep;
   lots = MathMax(lotsMin, MathMin(lotsMax, lots));

   return lots;
}

//====================================================================
//  PROTECTIONS
//====================================================================

//--- Vérifie le drawdown maximum
bool VerifierDrawdown()
{
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   if(g_balancePic <= 0) return false;

   double dd = ((g_balancePic - equity) / g_balancePic) * 100.0;

   if(dd >= DrawdownMaxPct)
   {
      FermerToutesPositions();
      g_eaArrete    = true;
      g_raisonArret = StringFormat("DRAWDOWN MAX %.2f%% atteint !", dd);
      Alert("[SmartEA] ARRÊTÉ – " + g_raisonArret);
      Print("[SmartEA] ARRÊTÉ – " + g_raisonArret);
      return true;
   }
   return false;
}

//--- Vérifie le bilan mensuel et la protection 6 mois consécutifs
bool VerifierMois()
{
   if(!Protection6Mois) return false;

   int moisCourant = (int)TimeMonth(TimeCurrent());
   if(moisCourant == g_moisSuivi) return false;

   double balActuelle = AccountInfoDouble(ACCOUNT_BALANCE);
   double perfMois    = 0;
   if(g_balanceDebutMois > 0)
      perfMois = ((balActuelle - g_balanceDebutMois) / g_balanceDebutMois) * 100.0;

   // Décaler l'historique (0 = plus récent)
   for(int i = 5; i > 0; i--)
      g_perfMensuelle[i] = g_perfMensuelle[i - 1];
   g_perfMensuelle[0] = perfMois;

   Print(StringFormat("[SmartEA] Mois %d terminé – Perf : %.2f%%", g_moisSuivi, perfMois));

   g_moisSuivi        = moisCourant;
   g_balanceDebutMois = balActuelle;

   // Vérifier 6 mois consécutifs négatifs
   bool sixMoisNegatifs = true;
   for(int i = 0; i < 6; i++)
   {
      if(g_perfMensuelle[i] >= 0) { sixMoisNegatifs = false; break; }
   }

   if(sixMoisNegatifs)
   {
      FermerToutesPositions();
      g_eaArrete    = true;
      g_raisonArret = "6 mois consécutifs en perte – Révision de stratégie requise";
      Alert("[SmartEA] ARRÊTÉ – " + g_raisonArret);
      Print("[SmartEA] ARRÊTÉ – " + g_raisonArret);
      return true;
   }
   return false;
}

//--- Vérifie les pertes consécutives
bool VerifierPertesConsec()
{
   if(g_pertesConsec >= PertesConsecMax)
   {
      if(!g_eaArrete)
      {
         g_eaArrete    = true;
         g_raisonArret = StringFormat("%d pertes consécutives – Pause trading", PertesConsecMax);
         Alert("[SmartEA] PAUSE – " + g_raisonArret);
         Print("[SmartEA] PAUSE – " + g_raisonArret);
      }
      return true;
   }
   return false;
}

//====================================================================
//  UTILITAIRES
//====================================================================

bool HeureTradingOK()
{
   int heure = (int)TimeHour(TimeCurrent());
   if(HeureDebut < HeureFin)
      return (heure >= HeureDebut && heure < HeureFin);
   else
      return (heure >= HeureDebut || heure < HeureFin);
}

double NormaliserPrix(double prix)
{
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   return NormalizeDouble(prix, digits);
}

int CompterPositions()
{
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(g_position.SelectByIndex(i))
         if(g_position.Magic() == MagicNumber && g_position.Symbol() == _Symbol)
            count++;
   }
   return count;
}

void FermerToutesPositions()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(!g_position.SelectByIndex(i))       continue;
      if(g_position.Magic()  != MagicNumber) continue;
      if(g_position.Symbol() != _Symbol)     continue;
      g_trade.PositionClose(g_position.Ticket());
   }
}

void AfficherStatut()
{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity  = AccountInfoDouble(ACCOUNT_EQUITY);
   double dd      = (g_balancePic > 0) ? ((g_balancePic - equity) / g_balancePic * 100.0) : 0;
   double perfMoisActuel = (g_balanceDebutMois > 0)
                         ? ((balance - g_balanceDebutMois) / g_balanceDebutMois * 100.0)
                         : 0;

   string statut = g_eaArrete ? ("ARRÊTÉ: " + g_raisonArret) : "EN COURS";
   string info = "─── SmartEA MT5 ───\n"
               + "Statut : " + statut + "\n"
               + "Balance : " + DoubleToString(balance, 2) + " "
               + AccountInfoString(ACCOUNT_CURRENCY) + "\n"
               + "Equity  : " + DoubleToString(equity, 2) + " "
               + AccountInfoString(ACCOUNT_CURRENCY) + "\n"
               + "Drawdown: " + DoubleToString(dd, 2) + "% (max "
               + DoubleToString(DrawdownMaxPct, 0) + "%)\n"
               + "Perf mois: " + DoubleToString(perfMoisActuel, 2) + "%\n"
               + "Pertes consec.: " + IntegerToString(g_pertesConsec)
               + "/" + IntegerToString(PertesConsecMax) + "\n"
               + "Positions: " + IntegerToString(CompterPositions());

   Comment(info);
}

//+------------------------------------------------------------------+
