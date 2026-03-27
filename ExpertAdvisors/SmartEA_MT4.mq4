//+------------------------------------------------------------------+
//|                                              SmartEA_MT4.mq4     |
//|                         CryptoRobot Expert Advisor - MT4         |
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
#property strict
#property description "SmartEA - Pullback Tendance | EMA + RSI + ADX | Gestion risque ATR"

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
input double RisquePercent   = 1.0;  // Risque par trade en % du capital
input int    ATR_Periode     = 14;   // Période ATR
input double ATR_Mult_SL     = 1.5;  // Multiplicateur ATR pour Stop Loss
input double ATR_Mult_TP     = 3.0;  // Multiplicateur ATR pour Take Profit
input bool   UtiliserTrailing = true; // Activer le Trailing Stop
input double ATR_Mult_Trail  = 1.2;  // Multiplicateur ATR pour Trailing Stop
input int    Slippage        = 3;    // Slippage maximal (points)

input string s3 = "======= PROTECTION ========";  // ──────────────
input double DrawdownMaxPct    = 15.0; // Drawdown max avant arrêt d'urgence (%)
input int    PertesConsecMax   = 6;    // Pertes consécutives max avant pause
input bool   Protection6Mois   = true; // Activer la protection 6 mois perdants
input bool   FiltreHeures      = true; // Filtrer les heures de trading
input int    HeureDebut        = 2;    // Heure début trading (serveur)
input int    HeureFin          = 22;   // Heure fin trading (serveur)

input string s4 = "======== GÉNÉRAL =========";  // ──────────────
input int    MagicNumber  = 20240101;  // Numéro magique unique de l'EA
input string Commentaire  = "SmartEA"; // Commentaire sur les ordres

//====================================================================
//  VARIABLES GLOBALES
//====================================================================

double g_balancePic         = 0;
double g_balanceDebutMois   = 0;
int    g_pertesConsec       = 0;
int    g_moisSuivi          = 0;
double g_perfMensuelle[6];   // Performances des 6 derniers mois (indice 0 = le plus récent)
bool   g_eaArrete           = false;
string g_raisonArret        = "";
int    g_dernierTicketVerif = -1;

//====================================================================
//  INITIALISATION
//====================================================================

int OnInit()
{
   g_balancePic       = AccountBalance();
   g_balanceDebutMois = AccountBalance();
   g_moisSuivi        = Month();
   g_pertesConsec     = 0;
   g_eaArrete         = false;
   ArrayInitialize(g_perfMensuelle, 1.0); // 1.0 = neutre (ni gain ni perte)

   Print("=== SmartEA MT4 démarré ===");
   Print("Capital : ", AccountBalance(), " ", AccountCurrency());
   Print("Risque par trade : ", RisquePercent, "%");
   Print("DrawdownMax : ", DrawdownMaxPct, "%");
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   Comment("");
   Print("=== SmartEA MT4 arrêté (code ", reason, ") ===");
}

//====================================================================
//  TICK PRINCIPAL
//====================================================================

void OnTick()
{
   // ── Affichage du statut sur le graphique ──
   AfficherStatut();

   if(g_eaArrete) return;

   // ── Mise à jour du pic de balance ──
   if(AccountBalance() > g_balancePic)
      g_balancePic = AccountBalance();

   // ── Vérifications de protection ──
   if(VerifierDrawdown())   return;
   if(VerifierMois())       return;
   if(VerifierPertesConsec()) return;

   // ── Filtre horaire ──
   if(FiltreHeures && !HeureTradingOK()) return;

   // ── Détecter les trades fermés depuis le dernier tick ──
   DetecterTradesFermes();

   // ── N'agir qu'à la clôture d'une nouvelle bougie ──
   static datetime derniereBarreTraitee = 0;
   if(Time[0] == derniereBarreTraitee) return;
   derniereBarreTraitee = Time[0];

   // ── Gestion du Trailing Stop sur positions ouvertes ──
   if(UtiliserTrailing)
      GererTrailingStop();

   // ── Chercher une entrée si aucune position ──
   if(CompterPositions() == 0)
      ChercherEntrees();
}

//====================================================================
//  LOGIQUE D'ENTRÉE
//====================================================================

void ChercherEntrees()
{
   // Indicateurs calculés sur la bougie FERMÉE (index 1)
   double emaR  = iMA(NULL, 0, EMA_Rapide,   0, MODE_EMA, PRICE_CLOSE, 1);
   double emaL  = iMA(NULL, 0, EMA_Lente,    0, MODE_EMA, PRICE_CLOSE, 1);
   double emaT  = iMA(NULL, 0, EMA_Tendance, 0, MODE_EMA, PRICE_CLOSE, 1);
   double rsi   = iRSI(NULL, 0, RSI_Periode, PRICE_CLOSE, 1);
   double adx   = iADX(NULL, 0, ADX_Periode, PRICE_CLOSE, MODE_MAIN, 1);
   double atr   = iATR(NULL, 0, ATR_Periode, 1);

   // Valeurs précédentes pour confirmer le croisement
   double emaRPrev = iMA(NULL, 0, EMA_Rapide, 0, MODE_EMA, PRICE_CLOSE, 2);
   double emaLPrev = iMA(NULL, 0, EMA_Lente,  0, MODE_EMA, PRICE_CLOSE, 2);

   // Filtre de tendance : marché doit être en mouvement directionnel
   if(adx < ADX_Min) return;
   if(atr <= 0)      return;

   //------------------------------------------------------------------
   //  SIGNAL ACHAT
   //  • Tendance haussière confirmée (prix > EMA200)
   //  • EMA rapide > EMA lente (momentum haussier)
   //  • Croisement haussier récent OU EMA rapide > lente avec RSI en survente
   //  • RSI en zone de survente (pullback sain en tendance)
   //------------------------------------------------------------------
   bool croisHaussier = (emaRPrev <= emaLPrev) && (emaR > emaL);
   bool pullbackAchat = (emaR > emaL) && (rsi >= RSI_Survente - 5) && (rsi <= RSI_Survente + 10);
   bool condAchat = (Close[1] > emaT) &&
                    (croisHaussier || pullbackAchat) &&
                    (rsi > 30) && (rsi < 55);

   //------------------------------------------------------------------
   //  SIGNAL VENTE
   //  • Tendance baissière confirmée (prix < EMA200)
   //  • EMA rapide < EMA lente (momentum baissier)
   //  • Croisement baissier récent OU RSI en surachat sur pullback
   //  • RSI en zone de surachat (pullback sain en tendance)
   //------------------------------------------------------------------
   bool croisBaissier  = (emaRPrev >= emaLPrev) && (emaR < emaL);
   bool pullbackVente  = (emaR < emaL) && (rsi <= RSI_Surachat + 5) && (rsi >= RSI_Surachat - 10);
   bool condVente = (Close[1] < emaT) &&
                    (croisBaissier || pullbackVente) &&
                    (rsi < 70) && (rsi > 45);

   //------------------------------------------------------------------
   //  OUVERTURE DES ORDRES
   //------------------------------------------------------------------
   if(condAchat)
   {
      double sl   = Ask - ATR_Mult_SL * atr;
      double tp   = Ask + ATR_Mult_TP * atr;
      double lots = CalculerLots(Ask - sl);
      if(lots <= 0) return;

      int ticket = OrderSend(Symbol(), OP_BUY, lots, Ask, Slippage,
                             NormaliserPrix(sl), NormaliserPrix(tp),
                             Commentaire, MagicNumber, 0, clrDeepSkyBlue);
      if(ticket > 0)
         Print("ACHAT ouvert #", ticket, " | Lots:", lots,
               " | SL:", NormaliserPrix(sl), " | TP:", NormaliserPrix(tp));
      else
         Print("Erreur ACHAT: ", GetLastError());
   }
   else if(condVente)
   {
      double sl   = Bid + ATR_Mult_SL * atr;
      double tp   = Bid - ATR_Mult_TP * atr;
      double lots = CalculerLots(sl - Bid);
      if(lots <= 0) return;

      int ticket = OrderSend(Symbol(), OP_SELL, lots, Bid, Slippage,
                             NormaliserPrix(sl), NormaliserPrix(tp),
                             Commentaire, MagicNumber, 0, clrOrangeRed);
      if(ticket > 0)
         Print("VENTE ouverte #", ticket, " | Lots:", lots,
               " | SL:", NormaliserPrix(sl), " | TP:", NormaliserPrix(tp));
      else
         Print("Erreur VENTE: ", GetLastError());
   }
}

//====================================================================
//  TRAILING STOP ATR
//====================================================================

void GererTrailingStop()
{
   double atr = iATR(NULL, 0, ATR_Periode, 1);
   if(atr <= 0) return;

   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != MagicNumber)           continue;
      if(OrderSymbol()      != Symbol())              continue;

      double nouveauSL;

      if(OrderType() == OP_BUY)
      {
         nouveauSL = NormaliserPrix(Bid - ATR_Mult_Trail * atr);
         // Déplacer SL seulement si nouveau SL est plus haut et en profit
         if(nouveauSL > OrderStopLoss() + Point && Bid > OrderOpenPrice())
            OrderModify(OrderTicket(), OrderOpenPrice(), nouveauSL,
                        OrderTakeProfit(), 0, clrGold);
      }
      else if(OrderType() == OP_SELL)
      {
         nouveauSL = NormaliserPrix(Ask + ATR_Mult_Trail * atr);
         // Déplacer SL seulement si nouveau SL est plus bas et en profit
         if((OrderStopLoss() == 0 || nouveauSL < OrderStopLoss() - Point)
             && Ask < OrderOpenPrice())
            OrderModify(OrderTicket(), OrderOpenPrice(), nouveauSL,
                        OrderTakeProfit(), 0, clrGold);
      }
   }
}

//====================================================================
//  CALCUL DE LA TAILLE DE POSITION (RISK % FIXE)
//====================================================================

double CalculerLots(double distanceSL)
{
   if(distanceSL <= 0) return 0;

   double balance      = AccountBalance();
   double risqueMontant = balance * (RisquePercent / 100.0);
   double tickValue    = MarketInfo(Symbol(), MODE_TICKVALUE);
   double tickSize     = MarketInfo(Symbol(), MODE_TICKSIZE);

   if(tickValue <= 0 || tickSize <= 0) return 0;

   // Nombre de ticks dans la distance SL
   double nbTicks = distanceSL / tickSize;
   double lots    = risqueMontant / (nbTicks * tickValue);

   // Normalisation selon contraintes broker
   double lotsMin  = MarketInfo(Symbol(), MODE_MINLOT);
   double lotsMax  = MarketInfo(Symbol(), MODE_MAXLOT);
   double lotsStep = MarketInfo(Symbol(), MODE_LOTSTEP);

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
   double equity = AccountEquity();
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

//--- Vérifie le bilan mensuel et la protection 6 mois
bool VerifierMois()
{
   if(!Protection6Mois) return false;

   int moisCourant = Month();
   if(moisCourant == g_moisSuivi) return false;

   // Nouveau mois : enregistrer la performance du mois écoulé
   double perfMois = 0;
   if(g_balanceDebutMois > 0)
      perfMois = ((AccountBalance() - g_balanceDebutMois) / g_balanceDebutMois) * 100.0;

   // Décaler l'historique
   for(int i = 5; i > 0; i--)
      g_perfMensuelle[i] = g_perfMensuelle[i - 1];
   g_perfMensuelle[0] = perfMois;

   Print(StringFormat("[SmartEA] Mois %d terminé – Perf : %.2f%%", g_moisSuivi, perfMois));

   // Réinitialiser pour le nouveau mois
   g_moisSuivi        = moisCourant;
   g_balanceDebutMois = AccountBalance();

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

//--- Détecte les nouveaux trades fermés pour mettre à jour g_pertesConsec
void DetecterTradesFermes()
{
   int total = OrdersHistoryTotal();
   if(total == 0) return;

   // Chercher le trade le plus récemment fermé appartenant à cet EA
   for(int i = total - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_HISTORY)) continue;
      if(OrderMagicNumber() != MagicNumber)            continue;
      if(OrderSymbol()      != Symbol())               continue;
      if(OrderType()        > OP_SELL)                 continue; // ignorer SL/TP virtuels

      int ticket = OrderTicket();
      if(ticket == g_dernierTicketVerif) break; // déjà traité

      g_dernierTicketVerif = ticket;

      double profit = OrderProfit() + OrderSwap() + OrderCommission();
      if(profit < 0)
         g_pertesConsec++;
      else
         g_pertesConsec = 0;

      Print(StringFormat("[SmartEA] Trade #%d fermé – Profit: %.2f | PertesConsec: %d",
                         ticket, profit, g_pertesConsec));
      break;
   }
}

//====================================================================
//  UTILITAIRES
//====================================================================

//--- Filtre horaire
bool HeureTradingOK()
{
   int heure = TimeHour(TimeCurrent());
   if(HeureDebut < HeureFin)
      return (heure >= HeureDebut && heure < HeureFin);
   else // passage minuit
      return (heure >= HeureDebut || heure < HeureFin);
}

//--- Normaliser un prix selon les décimales du symbole
double NormaliserPrix(double prix)
{
   return NormalizeDouble(prix, Digits);
}

//--- Compter les positions ouvertes de cet EA sur ce symbole
int CompterPositions()
{
   int count = 0;
   for(int i = 0; i < OrdersTotal(); i++)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() == MagicNumber && OrderSymbol() == Symbol())
         count++;
   }
   return count;
}

//--- Fermer toutes les positions de cet EA
void FermerToutesPositions()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != MagicNumber)           continue;
      if(OrderSymbol()      != Symbol())              continue;

      double prix = (OrderType() == OP_BUY) ? Bid : Ask;
      if(!OrderClose(OrderTicket(), OrderLots(), prix, Slippage, clrRed))
         Print("Erreur fermeture ordre #", OrderTicket(), " – ", GetLastError());
   }
}

//--- Affichage du statut sur le graphique
void AfficherStatut()
{
   double equity = AccountEquity();
   double dd     = (g_balancePic > 0) ? ((g_balancePic - equity) / g_balancePic * 100.0) : 0;
   double perfMoisActuel = (g_balanceDebutMois > 0)
                         ? ((AccountBalance() - g_balanceDebutMois) / g_balanceDebutMois * 100.0)
                         : 0;

   string statut = g_eaArrete ? ("ARRÊTÉ: " + g_raisonArret) : "EN COURS";
   string info = "─── SmartEA MT4 ───\n"
               + "Statut : " + statut + "\n"
               + "Balance : " + DoubleToStr(AccountBalance(), 2) + " " + AccountCurrency() + "\n"
               + "Equity  : " + DoubleToStr(equity, 2) + " " + AccountCurrency() + "\n"
               + "Drawdown: " + DoubleToStr(dd, 2) + "% (max " + DoubleToStr(DrawdownMaxPct, 0) + "%)\n"
               + "Perf mois: " + DoubleToStr(perfMoisActuel, 2) + "%\n"
               + "Pertes consec.: " + IntegerToString(g_pertesConsec) + "/" + IntegerToString(PertesConsecMax) + "\n"
               + "Positions: " + IntegerToString(CompterPositions());

   Comment(info);
}

//+------------------------------------------------------------------+
